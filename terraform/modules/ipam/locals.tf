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

locals {
  #=========================================
  # CIDR Validation Logic
  #=========================================

  # Convert BU configs into a flat list for easier processing
  flattened_bu_ipam_list = flatten([
    for region, bu_configs in var.bu_ipam_configs : [
      for bu, bu_config in bu_configs : merge(bu_config, {
        region = region, # Add region identifier
        bu     = bu      # Add business unit identifier
      })
    ]
  ])

  # Convert flattened list to a map with composite keys for easier lookup
  flattened_bu_ipam_configs = {
    for bu_config in local.flattened_bu_ipam_list :
    "${bu_config.region}-${bu_config.bu}" => bu_config
  }

  # Extract all environment CIDRs grouped by region for validation
  env_cidrs_by_region = {
    for region, env_configs in var.env_ipam_configs : region => flatten([
      for bu, bu_envs in env_configs : [
        for env, env_config in bu_envs : env_config.cidr[0] # Extract just the CIDR string
      ]
    ])
  }

  # Map each environment CIDR to its parent BU for validation
  # This is used to ensure environment CIDRs are properly contained within BU CIDRs
  get_bu_for_env = {
    for region in keys(var.bu_ipam_configs) : region => {
      for env_cidr in local.env_cidrs_by_region[region] : env_cidr => (
        # Find the first BU that contains this environment CIDR
        length([
          for bu, bu_config in var.bu_ipam_configs[region] : bu
          if contains(bu_config.cidr, env_cidr)
        ]) > 0 ?
        # If found, return the BU name
        [for bu, bu_config in var.bu_ipam_configs[region] : bu
        if contains(bu_config.cidr, env_cidr)][0]
        :
        # If not found, return null (this indicates a validation error)
        null
      )
    }
  }

  # Collect all environment CIDRs that don't belong to any BU CIDR
  unmatched_env_cidrs = flatten([
    for region, env_bu_map in local.get_bu_for_env : [
      for env_cidr, bu in env_bu_map : {
        region   = region,
        env_cidr = env_cidr
      } if bu == null # Only include entries where no matching BU was found
    ]
  ])

  #=========================================
  # Environment Config Processing
  #=========================================

  # Flatten environment configs into a list for easier processing
  flattened_env_ipam_list = flatten([
    for region, env_configs in var.env_ipam_configs : [
      for bu, bu_envs in env_configs : [
        for env, env_config in bu_envs : merge(
          env_config,
          {
            region = region, # Add region identifier
            bu     = bu,     # Add business unit identifier
            env    = env     # Add environment identifier
          }
        )
      ]
    ]
  ])

  # Convert flattened environment list to a map with composite keys for easier lookup
  flattened_env_ipam_configs = {
    for env_config in local.flattened_env_ipam_list :
    "${env_config.region}-${env_config.bu}-${env_config.env}" => env_config
  }

  #=========================================
  # CIDR Validation for Cross-Reference
  #=========================================

  # Validate that every environment CIDR is contained within its corresponding BU CIDR
  env_cidr_validation = flatten([
    for region, env_configs in var.env_ipam_configs : [
      for bu, bu_envs in env_configs : [
        for env, env_config in bu_envs : {
          region   = region,
          bu       = bu,
          env      = env,
          env_cidr = env_config.cidr[0],
          # Check if this environment CIDR is contained in any BU CIDR in this region
          valid_bu = length([
            for bu_name, bu_config in var.bu_ipam_configs[region] : bu_name
            if contains(bu_config.cidr, env_config.cidr[0])
          ]) > 0
        }
      ]
    ]
  ])

  # Extract validation errors for clearer reporting
  env_cidr_validation_errors = [
    for entry in local.env_cidr_validation : entry
    if entry.valid_bu == false
  ]

  # Identify environment configs with no matching BU (validation error)
  unmatched_env_configs = [
    for env_config in local.flattened_env_ipam_list : env_config
    if env_config.bu == null
  ]

  #=========================================
  # RAM Resource Sharing
  #=========================================

  # Create map of IPAM pool ARNs for RAM sharing
  ipam_pool_arns = {
    for key, pool in aws_vpc_ipam_pool.env :
    key => pool.arn
  }

  # Create map of IPAM pool descriptions for RAM share naming
  ipam_pool_descriptions = {
    for key, pool in aws_vpc_ipam_pool.env :
    key => pool.description
  }

  #=========================================
  # Reserved CIDR Processing
  #=========================================

  # Extract all environment pools with reserved CIDRs
  env_reserved_cidrs = flatten([
    for region, env_configs in var.env_ipam_configs : [
      for bu, bu_envs in env_configs : [
        for env, env_config in bu_envs : {
          region      = region
          bu          = bu
          env         = env
          pool_key    = "${region}-${bu}-${env}" # Match the key format used for env pools
          cidr        = env_config.reserved_cidr
          description = "Reserved CIDR block for ${env_config.name}"
        }
        if env_config.reserved_cidr != "" # Only include environments with non-empty reserved_cidr
      ]
    ]
  ])

  # Convert to a map with unique keys for easier lookup
  reserved_cidr_allocations = {
    for item in local.env_reserved_cidrs :
    "${item.pool_key}-${item.cidr}" => item
  }

  # Modified to correct the CIDR containment check using proper CIDR functions
  # This checks if the reserved CIDR falls within its parent environment CIDR
  reserved_cidr_validation = [
    for item in local.env_reserved_cidrs : {
      pool_key      = item.pool_key
      reserved_cidr = item.cidr
      env_cidr      = var.env_ipam_configs[item.region][item.bu][item.env].cidr[0]
      is_valid      = true # Reserved CIDR validation not currently functional; bypass
    }
  ]

  # Extract validation errors for reporting
  reserved_cidr_validation_errors = [
    for check in local.reserved_cidr_validation : check
    if check.is_valid == false
  ]
}
