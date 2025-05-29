import ipaddress
from typing import Dict, List, Any, Tuple, Optional, Set
from utils import get_region_display_name


def validate_inputs(
    top_cidr: str,
    regions: List[str],
    bus: List[str],
    envs: List[str],
    include_bu_level: bool = True,
    include_env_level: bool = True,
) -> Tuple[bool, str]:
    """
    Validate all user inputs before CIDR calculation.

    Args:
        top_cidr: The top-level CIDR block
        regions: List of AWS regions
        bus: List of business unit names
        envs: List of environment names
        include_bu_level: Whether to include business unit level
        include_env_level: Whether to include environment level

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Validate CIDR format
        network = ipaddress.IPv4Network(top_cidr)

        # Check if CIDR is private
        if not network.is_private:
            return (
                False,
                f"Top CIDR {top_cidr} should be in private IP space (10.0.0.0/8, 172.16.0.0/12, or 192.168.0.0/16)",
            )

        # Make sure we have at least one region
        if not regions:
            return False, "At least one AWS region must be selected"

        # Check if BU level is included
        if include_bu_level and not bus:
            return False, "At least one business unit must be specified"

        # Check if environment level is included
        if include_env_level and not envs:
            return False, "At least one environment must be specified"

        # Check if CIDR is large enough
        min_prefix = network.prefixlen

        # Calculate minimum required bits
        region_bits = max(0, (len(regions) - 1).bit_length())
        bu_bits = max(0, (len(bus) - 1).bit_length()) if include_bu_level else 0
        env_bits = max(0, (len(envs) - 1).bit_length()) if include_env_level else 0

        required_prefix = min_prefix + region_bits + bu_bits + env_bits

        # We'll target /18 as the smallest environment CIDR
        target_prefix = 18
        if required_prefix > target_prefix:
            return (
                False,
                f"Top CIDR {top_cidr} is too small for the requested hierarchy. Need at least a /{min_prefix - (required_prefix - target_prefix)} CIDR.",
            )

        return True, ""

    except ValueError as e:
        return False, f"Invalid CIDR format: {str(e)}"


def calculate_cidr_allocations(
    top_cidr: str,
    regions: List[str],
    bus: List[str] = None,
    envs: List[str] = None,
    include_bu_level: bool = True,
    include_env_level: bool = True,
    primary_region: Optional[str] = None,
    region_order: Optional[List[str]] = None,
    bu_order: Optional[List[str]] = None,
    env_order: Optional[List[str]] = None,
    environment_prefix_target: int = 18,
    reserved_strategy: str = "Half of subnet",
    reserved_percentage: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calculate CIDR allocations for the entire IPAM hierarchy with flexible levels.

    Args:
        top_cidr: The top-level CIDR block
        regions: List of AWS regions
        bus: List of business unit names (can be None if include_bu_level is False)
        envs: List of environment names (can be None if include_env_level is False)
        include_bu_level: Whether to include business unit level
        include_env_level: Whether to include environment level
        primary_region: The primary region for IPAM (defaults to first region)
        region_order: The order of regions for CIDR allocation
        bu_order: The order of business units for CIDR allocation
        env_order: The order of environments for CIDR allocation
        environment_prefix_target: Target prefix length for environment CIDRs
        reserved_strategy: Strategy for calculating reserved CIDRs ("Half of subnet" or "Custom percentage")
        reserved_percentage: If reserved_strategy is "Custom percentage", the percentage to reserve

    Returns:
        Dictionary with all CIDR allocations
    """
    # Apply ordering if provided
    if region_order:
        ordered_regions = [r for r in region_order if r in regions]
        # Add any regions not in the order
        ordered_regions.extend([r for r in regions if r not in ordered_regions])
        regions = ordered_regions

    if include_bu_level and bu_order and bus:
        ordered_bus = [b for b in bu_order if b in bus]
        # Add any BUs not in the order
        ordered_bus.extend([b for b in bus if b not in ordered_bus])
        bus = ordered_bus

    if include_env_level and env_order and envs:
        ordered_envs = [e for e in env_order if e in envs]
        # Add any environments not in the order
        ordered_envs.extend([e for e in envs if e not in ordered_envs])
        envs = ordered_envs

    # Ensure primary region is first if specified
    if primary_region and primary_region in regions:
        regions = [primary_region] + [r for r in regions if r != primary_region]

    # Parse the top-level CIDR
    top_network = ipaddress.IPv4Network(top_cidr)
    top_prefix_len = top_network.prefixlen

    # Calculate required regional prefix length
    # Each region needs a subnet that can accommodate all BUs/Envs
    required_regional_bits = max(0, (len(regions) - 1).bit_length())
    regional_prefix_len = top_prefix_len + required_regional_bits

    # Calculate regional CIDRs
    regional_subnets = list(top_network.subnets(new_prefix=regional_prefix_len))

    # Create results dictionary
    results = {"top_cidr": [top_cidr], "regional_cidrs": {}}

    # Add BU and ENV dictionaries if needed
    if include_bu_level:
        results["bu_cidrs"] = {}

    if include_env_level:
        results["env_cidrs"] = {}

    # Process each region
    for i, region in enumerate(regions):
        if i >= len(regional_subnets):
            raise ValueError(f"Not enough subnet space for region {region}")

        regional_cidr = str(regional_subnets[i])
        regional_network = ipaddress.IPv4Network(regional_cidr)

        results["regional_cidrs"][region] = {"cidr": [regional_cidr], "locale": region}

        # If we include BU level
        if include_bu_level and bus:
            # Calculate BU prefix length
            required_bu_bits = max(0, (len(bus) - 1).bit_length())
            bu_prefix_len = regional_network.prefixlen + required_bu_bits

            # Calculate BU CIDRs
            bu_subnets = list(regional_network.subnets(new_prefix=bu_prefix_len))

            results["bu_cidrs"][region] = {}

            # Process each BU
            for bu_idx, bu in enumerate(bus):
                if bu_idx >= len(bu_subnets):
                    raise ValueError(
                        f"Not enough subnet space for BU {bu} in region {region}"
                    )

                bu_cidr = str(bu_subnets[bu_idx])
                bu_network = ipaddress.IPv4Network(bu_cidr)

                results["bu_cidrs"][region][bu] = {"cidr": [bu_cidr]}

                # If we include environment level
                if include_env_level and envs:
                    # Calculate environment prefix length
                    required_env_bits = max(0, (len(envs) - 1).bit_length())
                    env_prefix_len = bu_network.prefixlen + required_env_bits

                    # Make sure the environment prefix isn't too long
                    if env_prefix_len > environment_prefix_target:
                        env_prefix_len = environment_prefix_target

                    # Calculate environment CIDRs
                    env_subnets = list(bu_network.subnets(new_prefix=env_prefix_len))

                    if region not in results["env_cidrs"]:
                        results["env_cidrs"][region] = {}

                    results["env_cidrs"][region][bu] = {}

                    # Process each environment
                    for env_idx, env in enumerate(envs):
                        if env_idx >= len(env_subnets):
                            raise ValueError(
                                f"Not enough subnet space for environment {env} in BU {bu}, region {region}"
                            )

                        env_cidr = str(env_subnets[env_idx])
                        env_network = ipaddress.IPv4Network(env_cidr)

                        # Calculate reserved CIDR based on strategy
                        if reserved_strategy == "Half of subnet":
                            # Calculate reserved CIDR (half of the environment CIDR)
                            reserved_prefix_len = env_network.prefixlen + 1
                            reserved_subnets = list(
                                env_network.subnets(new_prefix=reserved_prefix_len)
                            )
                            reserved_cidr = str(
                                reserved_subnets[1]
                            )  # Use the second half
                        else:  # "Custom percentage"
                            # Calculate reserved CIDR based on the specified percentage
                            percentage = (
                                reserved_percentage or 25
                            )  # Default to 25% if not specified

                            # Calculate how many subnets to create based on percentage
                            subnet_count = int(100 / percentage)
                            if subnet_count < 2:
                                subnet_count = 2  # Minimum is 2 subnets (50%)
                            if subnet_count > 10:
                                subnet_count = 10  # Maximum is 10 subnets (10%)

                            # Calculate the prefix length for the subnets
                            reserved_prefix_len = env_network.prefixlen + max(
                                1, (subnet_count - 1).bit_length()
                            )
                            reserved_subnets = list(
                                env_network.subnets(new_prefix=reserved_prefix_len)
                            )

                            # Use the last subnet as the reserved one
                            reserved_cidr = str(reserved_subnets[-1])

                        results["env_cidrs"][region][bu][env] = {
                            "cidr": [env_cidr],
                            "reserved_cidr": reserved_cidr,
                        }
        # If we skip BU level but include environment level
        elif include_env_level and envs:
            # Calculate environment prefix length directly from regional level
            required_env_bits = max(0, (len(envs) - 1).bit_length())
            env_prefix_len = regional_network.prefixlen + required_env_bits

            # Make sure the environment prefix isn't too long
            if env_prefix_len > environment_prefix_target:
                env_prefix_len = environment_prefix_target

            # Calculate environment CIDRs
            env_subnets = list(regional_network.subnets(new_prefix=env_prefix_len))

            if region not in results["env_cidrs"]:
                results["env_cidrs"][region] = {}

            # Use a placeholder BU name for consistency
            placeholder_bu = "Default"
            results["env_cidrs"][region][placeholder_bu] = {}

            # Process each environment
            for env_idx, env in enumerate(envs):
                if env_idx >= len(env_subnets):
                    raise ValueError(
                        f"Not enough subnet space for environment {env} in region {region}"
                    )

                env_cidr = str(env_subnets[env_idx])
                env_network = ipaddress.IPv4Network(env_cidr)

                # Calculate reserved CIDR based on strategy
                if reserved_strategy == "Half of subnet":
                    # Calculate reserved CIDR (half of the environment CIDR)
                    reserved_prefix_len = env_network.prefixlen + 1
                    reserved_subnets = list(
                        env_network.subnets(new_prefix=reserved_prefix_len)
                    )
                    reserved_cidr = str(reserved_subnets[1])  # Use the second half
                else:  # "Custom percentage"
                    # Calculate reserved CIDR based on the specified percentage
                    percentage = (
                        reserved_percentage or 25
                    )  # Default to 25% if not specified

                    # Calculate how many subnets to create based on percentage
                    subnet_count = int(100 / percentage)
                    if subnet_count < 2:
                        subnet_count = 2  # Minimum is 2 subnets (50%)
                    if subnet_count > 10:
                        subnet_count = 10  # Maximum is 10 subnets (10%)

                    # Calculate the prefix length for the subnets
                    reserved_prefix_len = env_network.prefixlen + max(
                        1, (subnet_count - 1).bit_length()
                    )
                    reserved_subnets = list(
                        env_network.subnets(new_prefix=reserved_prefix_len)
                    )

                    # Use the last subnet as the reserved one
                    reserved_cidr = str(reserved_subnets[-1])

                results["env_cidrs"][region][placeholder_bu][env] = {
                    "cidr": [env_cidr],
                    "reserved_cidr": reserved_cidr,
                }

    return results


def generate_resource_names(
    top_cidr: str,
    regions: List[str],
    bus: List[str] = None,
    envs: List[str] = None,
    include_bu_level: bool = True,
    include_env_level: bool = True,
) -> Dict[str, Any]:
    """
    Generate standardized names and descriptions for all IPAM resources with flexible levels.

    Args:
        top_cidr: The top-level CIDR block
        regions: List of AWS regions
        bus: List of business unit names
        envs: List of environment names
        include_bu_level: Whether to include business unit level
        include_env_level: Whether to include environment level

    Returns:
        Dictionary with all resource names and descriptions
    """
    # Top level
    top_name = "ipam-top"
    top_description = "Top-Level Multi-Region IPAM Pool"

    # Regional pools
    reg_names = {
        region: {
            "name": f"ipam-regional-{region}",
            "description": f"Regional IPAM Pool for {get_region_display_name(region)}",
        }
        for region in regions
    }

    # Initialize with empty dictionaries
    bu_names = {}
    env_names = {}

    # BU pools (if included)
    if include_bu_level and bus:
        bu_names = {
            region: {
                bu: {
                    "name": f"ipam-bu-{bu.lower()}-{region}",
                    "description": f"{bu} Business Unit IPAM Pool for {get_region_display_name(region)}",
                }
                for bu in bus
            }
            for region in regions
        }

    # Environment pools (if included)
    if include_env_level and envs:
        if include_bu_level and bus:
            # With BU level
            env_names = {
                region: {
                    bu: {
                        env: {
                            "name": f"ipam-{env.lower()}-{bu.lower()}-{region}",
                            "description": f"{env.capitalize()} Environment IPAM Pool for {bu} in {get_region_display_name(region)}",
                        }
                        for env in envs
                    }
                    for bu in bus
                }
                for region in regions
            }
        else:
            # Without BU level (using placeholder)
            placeholder_bu = "Default"
            env_names = {
                region: {
                    placeholder_bu: {
                        env: {
                            "name": f"ipam-{env.lower()}-{region}",
                            "description": f"{env.capitalize()} Environment IPAM Pool for {get_region_display_name(region)}",
                        }
                        for env in envs
                    }
                }
                for region in regions
            }

    return {
        "top": {"name": top_name, "description": top_description},
        "regional": reg_names,
        "business_units": bu_names,
        "environments": env_names,
    }


def generate_terraform_output(
    cidr_allocations: Dict[str, Any],
    resource_names: Dict[str, Any],
    include_bu_level: bool = True,
    include_env_level: bool = True,
) -> str:
    """
    Generate Terraform-compatible variable definitions with flexible levels.

    Args:
        cidr_allocations: Dictionary with calculated CIDR allocations
        resource_names: Dictionary with resource names and descriptions
        include_bu_level: Whether to include business unit level
        include_env_level: Whether to include environment level

    Returns:
        String with Terraform variable definitions
    """
    # Format regions list with double quotes
    regions_list = list(cidr_allocations["regional_cidrs"].keys())
    regions_str = "[" + ", ".join([f'"{region}"' for region in regions_list]) + "]"

    # Top-level configuration
    output = f"""provider_region   = "{regions_list[0]}"
operating_regions = {regions_str}
share_name = "global-aws-ipam-specification"
top_name        = "{resource_names['top']['name']}"
top_description = "{resource_names['top']['description']}"
top_cidr        = {format_cidr_list(cidr_allocations['top_cidr'])}
reg_ipam_configs = {{
"""

    # Regional pools
    for region, data in cidr_allocations["regional_cidrs"].items():
        output += f"""  {region} = {{
    name        = "{resource_names['regional'][region]['name']}"
    description = "{resource_names['regional'][region]['description']}"
    cidr        = {format_cidr_list(data['cidr'])}
    locale      = "{data['locale']}"
  }}
"""

    output += "}\n"

    # BU pools (if included)
    if (
        include_bu_level
        and "bu_cidrs" in cidr_allocations
        and cidr_allocations["bu_cidrs"]
    ):
        output += "bu_ipam_configs = {\n"

        for region, bus in cidr_allocations["bu_cidrs"].items():
            output += f"  {region} = {{\n"
            for bu, bu_data in bus.items():
                output += f"""    "{bu}" = {{
      name        = "{resource_names['business_units'][region][bu]['name']}"
      description = "{resource_names['business_units'][region][bu]['description']}"
      cidr        = {format_cidr_list(bu_data['cidr'])}
    }}
"""
            output += "  }\n"

        output += "}\n"
    else:
        # Empty BU config if not included
        output += "bu_ipam_configs = {}\n"

    # Environment pools (if included)
    if (
        include_env_level
        and "env_cidrs" in cidr_allocations
        and cidr_allocations["env_cidrs"]
    ):
        output += "env_ipam_configs = {\n"

        for region, bus in cidr_allocations["env_cidrs"].items():
            output += f"  {region} = {{\n"
            for bu, envs in bus.items():
                output += f"    {bu} = {{\n"
                for env, env_data in envs.items():
                    env_name = resource_names["environments"][region][bu][env]["name"]
                    env_description = resource_names["environments"][region][bu][env][
                        "description"
                    ]

                    output += f"""      {env} = {{
        name          = "{env_name}"
        description   = "{env_description}"
        cidr          = {format_cidr_list(env_data['cidr'])}
        reserved_cidr = "{env_data['reserved_cidr']}"
      }}
"""
                output += "    }\n"
            output += "  }\n"

        output += "}"
    else:
        # Empty environment config if not included
        output += "env_ipam_configs = {}"

    return output


def format_cidr_list(cidr_list: List[str]) -> str:
    """
    Format a list of CIDR strings for Terraform output with double quotes.

    Args:
        cidr_list: List of CIDR strings to format

    Returns:
        Formatted string with double quotes
    """
    return "[" + ", ".join([f'"{cidr}"' for cidr in cidr_list]) + "]"


def get_modified_terraform_module(
    include_bu_level: bool, include_env_level: bool
) -> str:
    """
    Generate modified Terraform module code based on the selected hierarchy.

    Args:
        include_bu_level: Whether to include business unit level
        include_env_level: Whether to include environment level

    Returns:
        String with modified Terraform module code
    """
    # No modifications needed if both levels are included (original design)
    if include_bu_level and include_env_level:
        return None

    # If BU level is skipped but ENV level is included
    if not include_bu_level and include_env_level:
        # Return modified module code that connects environments directly to regions
        return """# Modified module/ipam/main.tf for Region -> Environment hierarchy (skipping BU level)

# Note: Replace this section in your modules/ipam/main.tf file

########################################################
# Environment Pools (directly under Regional Pools)
########################################################

resource "aws_vpc_ipam_pool" "env" {
  for_each = local.flattened_env_ipam_configs

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
      ipam = "ipam-pool-${each.value.env}-${each.value.region}"
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

# Add this to modules/ipam/locals.tf

locals {
  # Flatten Environment IPAM configs into a list of objects (without BU level)
  flattened_env_ipam_list = flatten([
    for region, env_configs in var.env_ipam_configs : [
      for bu, bu_envs in env_configs : [
        for env, env_config in bu_envs : merge(
          env_config,
          {
            region = region,
            bu     = bu,
            env    = env
          }
        )
      ]
    ]
  ])

  # Convert the flattened list into a map
  flattened_env_ipam_configs = {
    for env_config in local.flattened_env_ipam_list :
    "${env_config.region}-${env_config.env}" => env_config
  }
}"""

    # If ENV level is skipped (with or without BU level)
    if not include_env_level:
        # Return appropriate message
        return """# No Terraform module modifications are needed if you're only skipping the Environment level.
# The existing module will work correctly with the modified input variables."""

    return None
