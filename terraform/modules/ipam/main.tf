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

#=======================================
# Multi-Region IPAM Resouce
#=======================================

resource "aws_vpc_ipam" "this" {
  description = var.top_description
  tier        = "advanced"

  dynamic "operating_regions" {
    for_each = var.operating_regions
    content {
      region_name = operating_regions.value
    }
  }

  # Merge existing tags with "ipam" tag
  tags = merge(
    var.tags,
    {
      ipam = "ipam-config"
    }
  )
}

#=======================================
# Top-Level Pool
#=======================================

resource "aws_vpc_ipam_pool" "top" {
  ipam_scope_id  = aws_vpc_ipam.this.private_default_scope_id
  description    = var.top_description
  address_family = "ipv4"
  auto_import    = false

  depends_on = [
    aws_vpc_ipam.this
  ]

  # Merge existing tags with "ipam" tag
  tags = merge(
    var.tags,
    {
      ipam = "ipam-pool-top-level"
    }
  )
}

resource "aws_vpc_ipam_pool_cidr" "top_cidr" {
  ipam_pool_id = aws_vpc_ipam_pool.top.id
  cidr         = var.top_cidr[0]

  depends_on = [
    aws_vpc_ipam_pool.top
  ]
}

#=======================================
# Regional Pools
#=======================================

resource "aws_vpc_ipam_pool" "regional" {
  for_each = var.reg_ipam_configs

  # ipam_scope_id       = aws_vpc_ipam_scope.private.id
  ipam_scope_id       = aws_vpc_ipam.this.private_default_scope_id
  description         = each.value.description
  address_family      = "ipv4"
  auto_import         = false
  locale              = each.value.locale
  source_ipam_pool_id = aws_vpc_ipam_pool.top.id

  depends_on = [
    aws_vpc_ipam_pool_cidr.top_cidr
  ]

  # Merge existing tags with "ipam" tag
  tags = merge(
    var.tags,
    {
      ipam = "ipam-pool-${each.value.locale}"
    }
  )
}

resource "aws_vpc_ipam_pool_cidr" "regional_cidr" {
  for_each = var.reg_ipam_configs

  ipam_pool_id = aws_vpc_ipam_pool.regional[each.key].id
  cidr         = each.value.cidr[0]

  depends_on = [
    aws_vpc_ipam_pool.regional
  ]
}

#=======================================
# Business Unit Pools
#=======================================

resource "aws_vpc_ipam_pool" "bu" {
  for_each = local.flattened_bu_ipam_configs

  ipam_scope_id       = aws_vpc_ipam.this.private_default_scope_id
  description         = each.value.description
  address_family      = "ipv4"
  auto_import         = false
  locale              = each.value.region
  source_ipam_pool_id = aws_vpc_ipam_pool.regional[each.value.region].id

  depends_on = [
    aws_vpc_ipam_pool_cidr.regional_cidr
  ]

  # Merge existing tags with "ipam" tag
  tags = merge(
    var.tags,
    {
      ipam = "ipam-pool-${each.value.bu}-${each.value.region}"
    }
  )
}

resource "aws_vpc_ipam_pool_cidr" "bu_cidr" {
  for_each = local.flattened_bu_ipam_configs

  ipam_pool_id = aws_vpc_ipam_pool.bu[each.key].id
  cidr         = each.value.cidr[0]

  depends_on = [
    aws_vpc_ipam_pool.bu
  ]
}

#=======================================
# Environment Pools
#=======================================

resource "aws_vpc_ipam_pool" "env" {
  for_each = local.flattened_env_ipam_configs

  ipam_scope_id       = aws_vpc_ipam.this.private_default_scope_id
  description         = each.value.description
  address_family      = "ipv4"
  auto_import         = true
  locale              = each.value.region
  source_ipam_pool_id = aws_vpc_ipam_pool.bu["${each.value.region}-${each.value.bu}"].id

  depends_on = [
    aws_vpc_ipam_pool_cidr.bu_cidr
  ]

  # Merge existing tags with "ipam" tag
  tags = merge(
    var.tags,
    {
      ipam = "ipam-pool-${each.value.bu}-${each.value.env}-${each.value.region}"
    }
  )
}

resource "aws_vpc_ipam_pool_cidr" "env_cidr" {
  for_each = local.flattened_env_ipam_configs

  ipam_pool_id = aws_vpc_ipam_pool.env[each.key].id
  cidr         = each.value.cidr[0]

  depends_on = [
    aws_vpc_ipam_pool.env
  ]
}

#=======================================
# Create RAM shares and associations
#=======================================

resource "aws_ram_resource_share" "ram_shares" {
  for_each = local.ipam_pool_arns

  name                      = replace(replace("RAM Share for ${local.ipam_pool_descriptions[each.key]}", "(", "- "), ")", "")
  allow_external_principals = false
  permission_arns           = ["arn:aws:ram::aws:permission/AWSRAMDefaultPermissionsIpamPool"]

  depends_on = [
    aws_vpc_ipam_pool_cidr.env_cidr
  ]
}

resource "aws_ram_principal_association" "ram_shares_prin_assoc" {
  for_each = aws_ram_resource_share.ram_shares

  principal          = var.organization_arn
  resource_share_arn = aws_ram_resource_share.ram_shares[each.key].arn

  depends_on = [
    aws_ram_resource_share.ram_shares
  ]
}

resource "aws_ram_resource_association" "share_assoc" {
  for_each = local.ipam_pool_arns

  resource_arn       = each.value
  resource_share_arn = aws_ram_resource_share.ram_shares[each.key].arn

  depends_on = [
    aws_ram_principal_association.ram_shares_prin_assoc
  ]
}

#=======================================
# Reserved CIDR Allocations
#=======================================

resource "aws_vpc_ipam_pool_cidr_allocation" "reserved_cidr" {
  for_each = local.reserved_cidr_allocations

  ipam_pool_id = aws_vpc_ipam_pool.env[each.value.pool_key].id
  cidr         = each.value.cidr
  description  = each.value.description

  # Precondition removed temporarily

  depends_on = [
    aws_vpc_ipam_pool_cidr.env_cidr
  ]
}
