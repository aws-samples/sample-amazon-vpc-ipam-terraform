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

## Resources

| Name | Type |
|------|------|
| [aws_ram_principal_association.ram_shares_prin_assoc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ram_principal_association) | resource |
| [aws_ram_resource_association.share_assoc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ram_resource_association) | resource |
| [aws_ram_resource_share.ram_shares](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ram_resource_share) | resource |
| [aws_vpc_ipam.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam) | resource |
| [aws_vpc_ipam_pool.bu](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool) | resource |
| [aws_vpc_ipam_pool.env](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool) | resource |
| [aws_vpc_ipam_pool.regional](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool) | resource |
| [aws_vpc_ipam_pool.top](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool) | resource |
| [aws_vpc_ipam_pool_cidr.bu_cidr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool_cidr) | resource |
| [aws_vpc_ipam_pool_cidr.env_cidr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool_cidr) | resource |
| [aws_vpc_ipam_pool_cidr.regional_cidr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool_cidr) | resource |
| [aws_vpc_ipam_pool_cidr.top_cidr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool_cidr) | resource |
| [aws_vpc_ipam_pool_cidr_allocation.reserved_cidr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_ipam_pool_cidr_allocation) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_bu_ipam_configs"></a> [bu\_ipam\_configs](#input\_bu\_ipam\_configs) | Configuration for Business Unit IPAM pools.<br/>Defines IP allocations for each business unit within each region.<br/>Organized as a map of regions to business units to configurations.<br/>Each business unit should receive a non-overlapping portion of its regional CIDR.<br/><br/>Example:<br/>{<br/>  us\_east\_1 = {<br/>    finance = {<br/>      name        = "Finance BU"<br/>      description = "Finance Business Unit Pool"<br/>      cidr        = ["10.0.0.0/14"]<br/>    }<br/>  }<br/>} | <pre>map(map(object({<br/>    name        = string  # Display name for the business unit pool<br/>    description = string  # Detailed description of the business unit pool's purpose<br/>    cidr        = list(string)  # List containing single CIDR allocation for this business unit<br/>  })))</pre> | n/a | yes |
| <a name="input_env_ipam_configs"></a> [env\_ipam\_configs](#input\_env\_ipam\_configs) | Configuration for environment-specific IPAM pools.<br/>Defines IP allocations for each environment within each business unit and region.<br/>Each environment should receive a non-overlapping portion of its parent business unit CIDR.<br/>The variable structure allows for flexible environment names to support various organizational structures.<br/><br/>Example:<br/>{<br/>  us\_east\_1 = {<br/>    finance = {<br/>      core = {<br/>        name          = "Finance Core"<br/>        description   = "Finance Core Infrastructure"<br/>        cidr          = ["10.0.0.0/16"]<br/>        reserved\_cidr = "10.0.0.0/24"  # Optional reserved block<br/>      }<br/>    }<br/>  }<br/>}<br/><br/>Note: The reserved\_cidr is an optional subnet that can be explicitly reserved within<br/>the environment CIDR block for specific purposes (e.g., shared services, gateways). | <pre>map(map(map(object({<br/>    name          = string  # Display name for the environment pool<br/>    description   = string  # Detailed description of the environment pool<br/>    cidr          = list(string)  # List containing single CIDR for this environment<br/>    reserved_cidr = string  # Optional CIDR to reserve within this environment<br/>  }))))</pre> | n/a | yes |
| <a name="input_operating_regions"></a> [operating\_regions](#input\_operating\_regions) | Regions where IPAM operates and manages resources.<br/>Must be valid AWS region names like us-east-1, eu-west-1, etc.<br/>At least one region must be specified. | `list(string)` | n/a | yes |
| <a name="input_organization_arn"></a> [organization\_arn](#input\_organization\_arn) | The ARN of the AWS Organization or specific account to share IPAM resources with.<br/>Typically this is the ARN of your entire AWS Organization.<br/>Format: arn:aws:organizations::<management-account-id>:organization/o-<organization-id> | `string` | n/a | yes |
| <a name="input_reg_ipam_configs"></a> [reg\_ipam\_configs](#input\_reg\_ipam\_configs) | Configuration for regional IPAM pools.<br/>Defines IP allocations for each AWS region where IPAM will operate.<br/>Each region should receive a non-overlapping portion of the top-level CIDR.<br/><br/>Example:<br/>{<br/>  us\_east\_1 = {<br/>    name        = "US East 1 Region"<br/>    description = "US East 1 Regional Pool"<br/>    cidr        = ["10.0.0.0/12"]<br/>    locale      = "us-east-1"<br/>  }<br/>} | <pre>map(object({<br/>    name        = string  # Display name for the regional pool<br/>    description = string  # Detailed description of the regional pool's purpose<br/>    cidr        = list(string)  # List containing single CIDR allocation for this region<br/>    locale      = string  # AWS region identifier (e.g., us-east-1)<br/>  }))</pre> | n/a | yes |
| <a name="input_share_name"></a> [share\_name](#input\_share\_name) | Name of the RAM share for IPAM resources.<br/>This name will be used to identify shared resources across accounts.<br/>Should be descriptive of the shared IPAM resource purpose. | `string` | n/a | yes |
| <a name="input_top_cidr"></a> [top\_cidr](#input\_top\_cidr) | CIDR block for the top-level IPAM pool.<br/>This represents your organization's entire IP address space.<br/>Example: ["10.0.0.0/8"] for a standard RFC1918 private address space.<br/>Only one CIDR block is currently supported at this level. | `list(string)` | n/a | yes |
| <a name="input_top_description"></a> [top\_description](#input\_top\_description) | Description of the top-level IPAM pool.<br/>Should provide context about the organizational IP space allocation strategy.<br/>This appears in the AWS console and helps administrators understand the pool's purpose. | `string` | n/a | yes |
| <a name="input_top_name"></a> [top\_name](#input\_top\_name) | Name of the top-level IPAM pool.<br/>This is the root pool that contains all regional allocations.<br/>Should be descriptive of your organization's entire IP space. | `string` | n/a | yes |
| <a name="input_tags"></a> [tags](#input\_tags) | Map of tags to apply to all resources created in the IPAM module.<br/>These tags will be applied to IPAM pools, RAM shares, and other resources.<br/>Used for resource governance, cost allocation, and operational visibility. | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_bu_cidrs"></a> [bu\_cidrs](#output\_bu\_cidrs) | Map of Business Unit IPAM pool CIDRs organized by region and business unit.<br/>Format: {region => {bu => cidr\_list}}<br/>These CIDR blocks define the address space available to each business unit within a region. |
| <a name="output_bu_pool_ids"></a> [bu\_pool\_ids](#output\_bu\_pool\_ids) | Map of Business Unit IPAM pool IDs keyed by region-bu composite identifier.<br/>Format: {region-bu => pool\_id}<br/>These pools are children of regional pools and represent business unit allocations. |
| <a name="output_env_cidrs"></a> [env\_cidrs](#output\_env\_cidrs) | Map of Environment IPAM pool CIDRs organized by region, business unit, and environment.<br/>Format: {region => {bu => {env => cidr\_list}}}<br/>These are the actual CIDR ranges available for VPC allocations in each environment.<br/>VPC CIDR allocations should be requested from these pools. |
| <a name="output_env_pool_ids"></a> [env\_pool\_ids](#output\_env\_pool\_ids) | Map of Environment IPAM pool IDs keyed by region-bu-env composite identifier.<br/>Format: {region-bu-env => pool\_id}<br/>These are the leaf-level pools used for allocating CIDRs to actual VPCs.<br/>Typical environments include: dev, qa, prod, and core. |
| <a name="output_ram_principal_associations"></a> [ram\_principal\_associations](#output\_ram\_principal\_associations) | Details of the RAM principal associations for the organization.<br/>Contains information about which principals (organization/accounts) have access to the shared resources.<br/>Format: {key => {resource\_share\_arn => arn, principal => principal\_id}}<br/>Used for auditing cross-account access permissions. |
| <a name="output_ram_resource_associations"></a> [ram\_resource\_associations](#output\_ram\_resource\_associations) | Details of RAM resource associations for IPAM pools.<br/>Contains information about which IPAM pools are shared via RAM.<br/>Format: {key => {association\_arn => arn, association\_id => id}}<br/>Used for tracking which resources are shared and their association identifiers. |
| <a name="output_ram_resource_share_arns"></a> [ram\_resource\_share\_arns](#output\_ram\_resource\_share\_arns) | Map of RAM resource share ARNs keyed by pool identifier.<br/>Format: {pool\_key => share\_arn}<br/>These resource shares enable cross-account access to IPAM pools. |
| <a name="output_regional_pool_ids"></a> [regional\_pool\_ids](#output\_regional\_pool\_ids) | Map of regional IPAM pool IDs keyed by region identifier.<br/>Format: {region\_key => pool\_id}<br/>These pools are direct children of the top-level pool and represent regional allocations. |
| <a name="output_top_pool_id"></a> [top\_pool\_id](#output\_top\_pool\_id) | The ID of the top-level IPAM pool that represents the organization's entire IP space.<br/>This is the root of the hierarchical pool structure. |
<!-- END_TF_DOCS -->