<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.9.1, < 2.5.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 5.11.0, < 6.11.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_business_unit"></a> [business\_unit](#input\_business\_unit) | Business Unit for the resource being deployed | `string` | n/a | yes |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment for the resource being deployed | `string` | n/a | yes |
| <a name="input_feature_name"></a> [feature\_name](#input\_feature\_name) | Feature name for the resource being deployed | `string` | n/a | yes |
| <a name="input_product_name"></a> [product\_name](#input\_product\_name) | Product name for the resource being deployed | `string` | n/a | yes |
| <a name="input_optional_tags"></a> [optional\_tags](#input\_optional\_tags) | Map of any non-required tags to include in the default tags. Will be appended to this module's tag\_map output. | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_tag_map"></a> [tag\_map](#output\_tag\_map) | Return the full map of all required and optional tags |
<!-- END_TF_DOCS -->