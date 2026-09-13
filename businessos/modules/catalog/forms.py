from django import forms

from businessos.core.reference.models import UnitOfMeasure

from .models import AttributeValue, Product, ProductCategory


class ProductCreateForm(forms.Form):
    name = forms.CharField(max_length=200)
    sku = forms.CharField(max_length=64, label="Initial SKU")
    structure = forms.ChoiceField(choices=Product.Structure.choices)
    product_type = forms.ChoiceField(choices=Product.Type.choices)
    category = forms.ModelChoiceField(queryset=ProductCategory.objects.none(), required=False)
    default_uom = forms.ModelChoiceField(queryset=UnitOfMeasure.objects.none())
    sales_description = forms.CharField(widget=forms.Textarea, required=False)
    purchase_description = forms.CharField(widget=forms.Textarea, required=False)
    is_sellable = forms.BooleanField(required=False, initial=True)
    is_purchasable = forms.BooleanField(required=False, initial=True)
    is_active = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = ProductCategory.objects.filter(
            company_id=company_id, is_active=True
        )
        self.fields["default_uom"].queryset = UnitOfMeasure.objects.filter(is_active=True)


class ProductEditForm(forms.Form):
    name = forms.CharField(max_length=200)
    sku = forms.CharField(max_length=64, label="SKU", required=False)
    product_type = forms.ChoiceField(choices=Product.Type.choices)
    category = forms.ModelChoiceField(queryset=ProductCategory.objects.none(), required=False)
    default_uom = forms.ModelChoiceField(queryset=UnitOfMeasure.objects.none())
    sales_description = forms.CharField(widget=forms.Textarea, required=False)
    purchase_description = forms.CharField(widget=forms.Textarea, required=False)
    is_sellable = forms.BooleanField(required=False)
    is_purchasable = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False)

    def __init__(self, *args, company_id, is_simple, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_simple:
            self.fields.pop("sku")
        self.fields["category"].queryset = ProductCategory.objects.filter(
            company_id=company_id, is_active=True
        )
        self.fields["default_uom"].queryset = UnitOfMeasure.objects.filter(is_active=True)


class CategoryForm(forms.Form):
    name = forms.CharField(max_length=160)
    parent = forms.ModelChoiceField(queryset=ProductCategory.objects.none(), required=False)
    is_active = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = ProductCategory.objects.filter(
            company_id=company_id, is_active=True
        )


class VariantForm(forms.Form):
    sku = forms.CharField(max_length=64)
    is_default = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False, initial=True)


class AttributeForm(forms.Form):
    name = forms.CharField(max_length=120)
    is_active = forms.BooleanField(required=False, initial=True)


class AttributeValueForm(forms.Form):
    value = forms.CharField(max_length=120)
    is_active = forms.BooleanField(required=False, initial=True)


class VariantAttributeForm(forms.Form):
    attribute_values = forms.ModelMultipleChoiceField(
        queryset=AttributeValue.objects.none(), required=False, widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attribute_values"].queryset = AttributeValue.objects.filter(
            company_id=company_id, is_active=True, attribute__is_active=True
        ).select_related("attribute")
