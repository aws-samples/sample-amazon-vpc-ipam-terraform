<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.9.1, < 2.5.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 5.11.0, < 6.11.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 5.11.0, < 6.11.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_ipam"></a> [ipam](#module\_ipam) | ./modules/ipam | n/a |
| <a name="module_tags"></a> [tags](#module\_tags) | ./modules/tags | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_organizations_organization.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/organizations_organization) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_bu_ipam_configs"></a> [bu\_ipam\_configs](#input\_bu\_ipam\_configs) | Configuration for Business Unit IPAM pools.<br/>Defines IP allocations for each business unit within each region.<br/>Organized as a map of regions to business units to configurations.<br/>Each business unit should receive a non-overlapping portion of its regional CIDR.<br/><br/>Example:<br/>{<br/>  us\_east\_1 = {<br/>    finance = {<br/>      name        = "Finance BU"<br/>      description = "Finance Business Unit Pool"<br/>      cidr        = ["10.0.0.0/14"]<br/>    }<br/>  }<br/>} | <pre>map(map(object({<br/>    name        = string  # Display name for the business unit pool<br/>    description = string  # Detailed description of the business unit pool's purpose<br/>    cidr        = list(string)  # List containing single CIDR allocation for this business unit<br/>  })))</pre> | n/a | yes |
| <a name="input_env_ipam_configs"></a> [env\_ipam\_configs](#input\_env\_ipam\_configs) | Configuration for environment-specific IPAM pools within each business unit and region.<br/>Defines IP allocations for each environment within each business unit and region.<br/>Each environment should receive a non-overlapping portion of its parent business unit CIDR.<br/><br/>Example:<br/>{<br/>  us\_east\_1 = {<br/>    finance = {<br/>      core = {<br/>        name          = "Finance Core"<br/>        description   = "Finance Core Infrastructure"<br/>        cidr          = ["10.0.0.0/16"]<br/>        reserved\_cidr = "10.0.0.0/24"  # Optional reserved block<br/>      }<br/>    }<br/>  }<br/>}<br/><br/>Note: The reserved\_cidr is an optional subnet that can be explicitly reserved within<br/>the environment CIDR block for specific purposes (e.g., shared services, gateways). | <pre>map(map(map(object({<br/>    name          = string  # Display name for the environment pool<br/>    description   = string  # Detailed description of the environment pool<br/>    cidr          = list(string)  # List containing single CIDR for this environment<br/>    reserved_cidr = string  # Optional CIDR to reserve within this environment<br/>  }))))</pre> | n/a | yes |
| <a name="input_operating_regions"></a> [operating\_regions](#input\_operating\_regions) | Regions where IPAM operates and manages resources.<br/>Must be valid AWS region names like us-east-1, eu-west-1, etc.<br/>At least one region must be specified. | `list(string)` | n/a | yes |
| <a name="input_provider_region"></a> [provider\_region](#input\_provider\_region) | AWS region where IPAM will be deployed and managed. | `string` | n/a | yes |
| <a name="input_reg_ipam_configs"></a> [reg\_ipam\_configs](#input\_reg\_ipam\_configs) | Configuration for regional IPAM pools.<br/>Defines IP allocations for each AWS region where IPAM will operate.<br/>Each region should receive a non-overlapping portion of the top-level CIDR.<br/><br/>Example:<br/>{<br/>  us\_east\_1 = {<br/>    name        = "US East 1 Region"<br/>    description = "US East 1 Regional Pool"<br/>    cidr        = ["10.0.0.0/12"]<br/>    locale      = "us-east-1"<br/>  }<br/>} | <pre>map(object({<br/>    name        = string  # Display name for the regional pool<br/>    description = string  # Detailed description of the regional pool's purpose<br/>    cidr        = list(string)  # List containing single CIDR allocation for this region<br/>    locale      = string  # AWS region identifier (e.g., us-east-1)<br/>  }))</pre> | n/a | yes |
| <a name="input_share_name"></a> [share\_name](#input\_share\_name) | Name of the RAM share for IPAM resources.<br/>This name will be used to identify shared resources across accounts.<br/>Should be descriptive of the shared IPAM resource purpose. | `string` | n/a | yes |
| <a name="input_top_cidr"></a> [top\_cidr](#input\_top\_cidr) | CIDR block for the top-level IPAM pool.<br/>This represents your organization's entire IP address space.<br/>Example: ["10.0.0.0/8"] for a standard RFC1918 private address space.<br/>Only one CIDR block is currently supported at this level. | `list(string)` | n/a | yes |
| <a name="input_top_description"></a> [top\_description](#input\_top\_description) | Description of the top-level IPAM pool.<br/>Should provide context about the organizational IP space allocation strategy.<br/>This appears in the AWS console and helps administrators understand the pool's purpose. | `string` | n/a | yes |
| <a name="input_top_name"></a> [top\_name](#input\_top\_name) | Name of the top-level IPAM pool.<br/>This is the root pool that contains all regional allocations.<br/>Should be descriptive of your organization's entire IP space. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_ipam_bu_pool_cidrs"></a> [ipam\_bu\_pool\_cidrs](#output\_ipam\_bu\_pool\_cidrs) | Map of Business Unit IPAM pool CIDRs organized by region and BU.<br/>Format: {region => {bu => cidr\_list}}<br/>Example: {"us-east-1" => {"finance" => ["10.0.0.0/14"]}}<br/>Use these for network planning and documentation purposes. |
| <a name="output_ipam_bu_pool_ids"></a> [ipam\_bu\_pool\_ids](#output\_ipam\_bu\_pool\_ids) | Map of Business Unit IPAM pool IDs keyed by region-bu composite identifier.<br/>Format: {region-bu => pool\_id}<br/>Example: {"us-east-1-finance" => "ipam-pool-0123456789abcdef"}<br/>Use these IDs when referencing business unit-specific address allocations. |
| <a name="output_ipam_env_pool_cidrs"></a> [ipam\_env\_pool\_cidrs](#output\_ipam\_env\_pool\_cidrs) | Map of Environment IPAM pool CIDRs organized by region, BU, and environment.<br/>Format: {region => {bu => {env => cidr\_list}}}<br/>Example: {"us-east-1" => {"finance" => {"dev" => ["10.0.0.0/16"]}}}<br/>These are the actual CIDR ranges available for VPC allocations in each environment. |
| <a name="output_ipam_env_pool_ids"></a> [ipam\_env\_pool\_ids](#output\_ipam\_env\_pool\_ids) | Map of Environment IPAM pool IDs keyed by region-bu-env composite identifier.<br/>Format: {region-bu-env => pool\_id}<br/>Example: {"us-east-1-finance-dev" => "ipam-pool-0123456789abcdef"}<br/>These are the leaf-level pools used for allocating CIDRs to actual VPCs.<br/><br/>Usage example:<pre>module "vpc" {<br/>  source = "./modules/vpc"<br/>  ipam_pool_id = module.ipam.ipam_env_pool_ids["us-east-1-finance-dev"]<br/>}</pre> |
| <a name="output_ipam_ram_principal_associations"></a> [ipam\_ram\_principal\_associations](#output\_ipam\_ram\_principal\_associations) | Details of the RAM principal associations for the organization.<br/>Contains information about which principals (organization/accounts) have access to the shared resources.<br/>Format: {key => {resource\_share\_arn => arn, principal => principal\_id}} |
| <a name="output_ipam_ram_resource_associations"></a> [ipam\_ram\_resource\_associations](#output\_ipam\_ram\_resource\_associations) | Details of RAM resource associations for IPAM pools, including ARNs and IDs.<br/>Contains information about which IPAM pools are shared and their association details.<br/>Format: {key => {association\_arn => arn, association\_id => id}}<br/><br/>These details are useful for troubleshooting cross-account access issues or auditing resource sharing. |
| <a name="output_ipam_ram_resource_share_arns"></a> [ipam\_ram\_resource\_share\_arns](#output\_ipam\_ram\_resource\_share\_arns) | The ARNs of the RAM resource shares for IPAM pools.<br/>Format: {pool\_key => share\_arn}<br/>These ARNs can be used to reference the RAM shares in IAM policies or other AWS resources. |
| <a name="output_ipam_regional_pool_ids"></a> [ipam\_regional\_pool\_ids](#output\_ipam\_regional\_pool\_ids) | Map of regional IPAM pool IDs keyed by region identifier.<br/>Format: {region\_key => pool\_id}<br/>Example: {"us\_east\_1" => "ipam-pool-0123456789abcdef"}<br/>Use these IDs when referencing region-specific address allocations. |
| <a name="output_ipam_top_pool_id"></a> [ipam\_top\_pool\_id](#output\_ipam\_top\_pool\_id) | The ID of the top-level IPAM pool.<br/>Use this ID when referencing the entire organizational address space.<br/>Useful for administrative tasks affecting the entire IPAM hierarchy. |
<!-- END_TF_DOCS -->