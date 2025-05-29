#==============================================================================
# Sample Terraform Implementation for Hierarchical IPAM on AWS
#
# This code demonstrates how to implement hierarchical IP Address Management
# across multiple AWS regions, business units, and environments.
#
# IMPORTANT: This code is provided as a sample for educational purposes.
# Before using in production, review security configurations and customize
# to meet your organizational requirements.
#==============================================================================

module "ipam" {
  source  = "./modules/ipam"
  top_name          = var.top_name
  top_description   = var.top_description
  top_cidr          = var.top_cidr
  reg_ipam_configs  = var.reg_ipam_configs
  bu_ipam_configs   = var.bu_ipam_configs
  env_ipam_configs  = var.env_ipam_configs
  operating_regions = var.operating_regions
  organization_arn  = data.aws_organizations_organization.current.arn
  share_name        = var.share_name
  tags              = module.tags.tag_map
}
