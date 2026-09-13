from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render

from businessos.core.access.context import business_context_from_request

from .forms import (
    AttributeForm,
    AttributeValueForm,
    CategoryForm,
    ProductCreateForm,
    ProductEditForm,
    VariantAttributeForm,
    VariantForm,
)
from .models import Attribute, Product, ProductVariant
from .selectors import (
    active_categories,
    attributes_for_company,
    product_detail,
    products_for_company,
)
from .services import (
    assign_variant_attribute_values,
    create_attribute,
    create_attribute_value,
    create_category,
    create_product_variant,
    create_simple_product,
    create_variable_product,
    update_product,
    update_product_variant,
)


def _add_service_error(form, error):
    if hasattr(error, "message_dict"):
        for field, errors in error.message_dict.items():
            target = field if field in form.fields else None
            for message in errors:
                form.add_error(target, message)
    else:
        form.add_error(None, error)


def _product_service_data(cleaned_data):
    data = cleaned_data.copy()
    category = data.pop("category")
    data["category_id"] = category.id if category else None
    data["default_uom_id"] = data.pop("default_uom").id
    return data


@login_required
def product_list(request):
    context = business_context_from_request(request)
    search = request.GET.get("q", "")
    product_type = request.GET.get("type", "")
    return render(
        request,
        "catalog/product_list.html",
        {
            "products": products_for_company(
                context, search=search, product_type=product_type
            ),
            "search": search,
            "selected_type": product_type,
            "product_types": Product.Type.choices,
        },
    )


@login_required
def product_create(request):
    context = business_context_from_request(request)
    form = ProductCreateForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        data = _product_service_data(form.cleaned_data)
        structure = data.pop("structure")
        sku = data.pop("sku")
        try:
            if structure == Product.Structure.SIMPLE:
                product = create_simple_product(context, sku=sku, **data)
            else:
                product = create_variable_product(
                    context,
                    variants=[{"sku": sku, "is_default": True}],
                    **data,
                )
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Product and initial variant created.")
            return redirect("catalog:product_detail", product_id=product.id)
    return render(request, "catalog/product_form.html", {"form": form, "heading": "Create product"})


@login_required
def product_edit(request, product_id):
    context = business_context_from_request(request)
    try:
        product = product_detail(context, product_id=product_id)
    except Product.DoesNotExist as exc:
        raise Http404 from exc
    initial = {
        "name": product.name,
        "sku": product.variants.get().sku if product.structure == Product.Structure.SIMPLE else "",
        "product_type": product.product_type,
        "category": product.category_id,
        "default_uom": product.default_uom_id,
        "sales_description": product.sales_description,
        "purchase_description": product.purchase_description,
        "is_sellable": product.is_sellable,
        "is_purchasable": product.is_purchasable,
        "is_active": product.is_active,
    }
    form = ProductEditForm(
        request.POST or None,
        company_id=context.company_id,
        is_simple=product.structure == Product.Structure.SIMPLE,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_product(
                context, product_id=product.id, **_product_service_data(form.cleaned_data)
            )
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Product updated.")
            return redirect("catalog:product_detail", product_id=product.id)
    return render(request, "catalog/product_form.html", {"form": form, "heading": "Edit product"})


@login_required
def product_detail_view(request, product_id):
    context = business_context_from_request(request)
    try:
        product = product_detail(context, product_id=product_id)
    except Product.DoesNotExist as exc:
        raise Http404 from exc
    return render(request, "catalog/product_detail.html", {"product": product})


@login_required
def variant_create(request, product_id):
    context = business_context_from_request(request)
    form = VariantForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        try:
            create_product_variant(context, product_id=product_id, **form.cleaned_data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Variant created.")
            return redirect("catalog:product_detail", product_id=product_id)
    return render(request, "catalog/related_form.html", {"form": form, "heading": "Add variant"})


@login_required
def variant_edit(request, product_id, variant_id):
    context = business_context_from_request(request)
    try:
        variant = ProductVariant.objects.get(
            id=variant_id, product_id=product_id, company_id=context.company_id
        )
    except ProductVariant.DoesNotExist as exc:
        raise Http404 from exc
    form = VariantForm(
        request.POST or None,
        company_id=context.company_id,
        initial={
            "sku": variant.sku,
            "is_default": variant.is_default,
            "is_active": variant.is_active,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_product_variant(context, variant_id=variant.id, **form.cleaned_data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Variant updated.")
            return redirect("catalog:product_detail", product_id=product_id)
    return render(request, "catalog/related_form.html", {"form": form, "heading": "Edit variant"})


@login_required
def variant_attributes(request, product_id, variant_id):
    context = business_context_from_request(request)
    try:
        variant = ProductVariant.objects.get(
            id=variant_id, product_id=product_id, company_id=context.company_id
        )
    except ProductVariant.DoesNotExist as exc:
        raise Http404 from exc
    initial = {"attribute_values": variant.attribute_assignments.values_list(
        "attribute_value_id", flat=True
    )}
    form = VariantAttributeForm(
        request.POST or None, company_id=context.company_id, initial=initial
    )
    if request.method == "POST" and form.is_valid():
        try:
            assign_variant_attribute_values(
                context,
                variant_id=variant.id,
                attribute_value_ids=[value.id for value in form.cleaned_data["attribute_values"]],
            )
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Variant attributes updated.")
            return redirect("catalog:product_detail", product_id=product_id)
    return render(
        request,
        "catalog/related_form.html",
        {"form": form, "heading": f"Assign attributes · {variant.sku}"},
    )


@login_required
def category_list(request):
    context = business_context_from_request(request)
    form = CategoryForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        parent = data.pop("parent")
        data["parent_id"] = parent.id if parent else None
        try:
            create_category(context, **data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Category created.")
            return redirect("catalog:categories")
    return render(
        request,
        "catalog/category_list.html",
        {"form": form, "categories": active_categories(context)},
    )


@login_required
def attribute_list(request):
    context = business_context_from_request(request)
    form = AttributeForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        try:
            create_attribute(context, **form.cleaned_data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Attribute created.")
            return redirect("catalog:attributes")
    return render(
        request,
        "catalog/attribute_list.html",
        {"form": form, "attributes": attributes_for_company(context)},
    )


@login_required
def attribute_value_create(request, attribute_id):
    context = business_context_from_request(request)
    try:
        attribute = Attribute.objects.get(id=attribute_id, company_id=context.company_id)
    except Attribute.DoesNotExist as exc:
        raise Http404 from exc
    form = AttributeValueForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        try:
            create_attribute_value(context, attribute_id=attribute.id, **form.cleaned_data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Attribute value created.")
            return redirect("catalog:attributes")
    return render(
        request,
        "catalog/related_form.html",
        {"form": form, "heading": f"Add value · {attribute.name}"},
    )
