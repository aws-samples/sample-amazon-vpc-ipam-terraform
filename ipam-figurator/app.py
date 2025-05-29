import streamlit as st
import ipaddress
from typing import List, Dict, Any
import time
import plotly.express as px

# Import local modules
import ipam_logic
import utils


def main():
    # Set page config
    st.set_page_config(
        page_title="AWS IPAM Configurator", page_icon="🌐", layout="wide"
    )

    # App header
    st.title("AWS IPAM Configurator")
    st.markdown(
        """
    Generate Terraform configuration for AWS IP Address Manager (IPAM) with hierarchical pools.
    This tool helps you create properly structured CIDR allocations for multi-region,
    multi-business unit, multi-environment deployments.
    """
    )

    # Initialize session state variables if they don't exist
    if "cidr_allocations" not in st.session_state:
        st.session_state.cidr_allocations = None
    if "resource_names" not in st.session_state:
        st.session_state.resource_names = None
    if "terraform_output" not in st.session_state:
        st.session_state.terraform_output = None
    if "terraform_module_modifications" not in st.session_state:
        st.session_state.terraform_module_modifications = None
    if "calculation_complete" not in st.session_state:
        st.session_state.calculation_complete = False
    if "show_advanced" not in st.session_state:
        st.session_state.show_advanced = False
    if "selected_regions" not in st.session_state:
        st.session_state.selected_regions = []
    if "business_units" not in st.session_state:
        st.session_state.business_units = ["abc", "xyz"]
    if "environments" not in st.session_state:
        st.session_state.environments = ["core", "prod", "dev", "qa"]
    if "include_bu_level" not in st.session_state:
        st.session_state.include_bu_level = True
    if "include_env_level" not in st.session_state:
        st.session_state.include_env_level = True
    if "primary_region" not in st.session_state:
        st.session_state.primary_region = None
    if "reserved_strategy" not in st.session_state:
        st.session_state.reserved_strategy = "Half of subnet"
    if "reserved_percentage" not in st.session_state:
        st.session_state.reserved_percentage = 25
    if "env_prefix_target" not in st.session_state:
        st.session_state.env_prefix_target = 18

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "1. Configuration",
            "2. Organization",
            "3. Visualization",
            "4. Terraform Output",
        ]
    )

    with tab1:
        # Configuration inputs
        st.header("IPAM Configuration")

        with st.expander("About IPAM Configuration", expanded=True):
            st.markdown(
                """
            Amazon VPC IP Address Manager (IPAM) helps you plan, track, and monitor IP addresses for your AWS workloads.
            This tool creates a hierarchical structure with:

            1. **Top-Level Pool**: Global IP space for your organization
            2. **Regional Pools**: Subdivided by AWS region
            3. **Business Unit Pools** (Optional): Further subdivided for different business units
            4. **Environment Pools** (Optional): The most granular level for development, testing, production, etc.

            The tool will calculate appropriate CIDR ranges based on your selections.
            """
            )

        # Top-level CIDR input
        st.subheader("Step 1: Define Top-Level CIDR")
        top_cidr_col1, top_cidr_col2 = st.columns([3, 1])

        with top_cidr_col1:
            top_cidr = st.text_input(
                "Top-Level CIDR Block",
                value="10.192.0.0/12",
                help="The top-level CIDR block for your entire IPAM hierarchy (e.g., 10.0.0.0/8)",
            )

        with top_cidr_col2:
            # Add a quick CIDR validator that shows info about the entered CIDR
            if top_cidr:
                try:
                    network = ipaddress.IPv4Network(top_cidr)
                    st.metric("Total IPs", utils.format_ip_count(network.num_addresses))
                    if not network.is_private:
                        st.error("⚠️ Not a private IP range")
                    else:
                        st.success("✅ Valid private CIDR")
                except ValueError:
                    st.error("Invalid CIDR format")

        # Pool hierarchy configuration
        st.subheader("Step 2: Configure Pool Hierarchy")

        # Configure which levels to include
        hierarchy_col1, hierarchy_col2 = st.columns(2)

        with hierarchy_col1:
            st.write("**Select Pool Levels to Include**")
            st.write("Top-Level and Regional pools are always included.")

            include_bu_level = st.checkbox(
                "Include Business Unit Level", value=st.session_state.include_bu_level
            )
            st.session_state.include_bu_level = include_bu_level

        with hierarchy_col2:
            st.write("")  # For alignment
            st.write("")  # For alignment

            include_env_level = st.checkbox(
                "Include Environment Level", value=st.session_state.include_env_level
            )
            st.session_state.include_env_level = include_env_level

        # Region selection
        st.subheader("Step 3: Select AWS Regions")
        st.markdown("Select the AWS regions where you'll deploy resources.")

        # Get all regions that support IPAM
        ipam_regions = utils.get_ipam_regions()

        # Create two columns for region selection
        region_col1, region_col2 = st.columns(2)

        selected_regions = []

        with region_col1:
            st.write("**Primary IPAM Region**")
            primary_region = st.selectbox(
                "Select the primary region for IPAM",
                [region["code"] for region in ipam_regions],
                index=0,
                format_func=utils.get_region_display_name,
            )
            st.session_state.primary_region = primary_region
            selected_regions.append(primary_region)

            st.write("**North America & South America Regions**")
            americas_regions = [
                r for r in ipam_regions if r["code"].startswith(("us-", "ca-", "sa-"))
            ]
            for region in americas_regions:
                if region["code"] != primary_region and st.checkbox(
                    f"{region['name']} ({region['code']})",
                    value=region["code"] in st.session_state.selected_regions,
                ):
                    selected_regions.append(region["code"])

        with region_col2:
            st.write("**Europe, Middle East & Africa Regions**")
            emea_regions = [
                r for r in ipam_regions if r["code"].startswith(("eu-", "me-", "af-"))
            ]
            for region in emea_regions:
                if region["code"] != primary_region and st.checkbox(
                    f"{region['name']} ({region['code']})",
                    value=region["code"] in st.session_state.selected_regions,
                ):
                    selected_regions.append(region["code"])

            st.write("**Asia Pacific Regions**")
            apac_regions = [r for r in ipam_regions if r["code"].startswith("ap-")]
            for region in apac_regions:
                if region["code"] != primary_region and st.checkbox(
                    f"{region['name']} ({region['code']})",
                    value=region["code"] in st.session_state.selected_regions,
                ):
                    selected_regions.append(region["code"])

        st.session_state.selected_regions = selected_regions

        # Business Unit input (if BU level is included)
        if include_bu_level:
            st.subheader("Step 4: Define Business Units")
            st.markdown(
                "Enter the names of your business units. These will be used to create dedicated IP pools."
            )

            # Get existing BUs
            business_units = st.session_state.business_units.copy()

            # Create a column layout for BU input
            bu_cols = st.columns(3)

            # Display existing BUs
            new_business_units = []
            for i in range(len(business_units)):
                with bu_cols[i % 3]:
                    bu_key = f"bu_{i}"
                    bu_input = st.text_input(
                        f"Business Unit {i+1}", value=business_units[i], key=bu_key
                    )
                    if bu_input.strip():
                        new_business_units.append(bu_input.strip())

            # Button to add more BUs with unique key
            if st.button("Add Another Business Unit", key="add_bu_btn"):
                st.session_state.business_units.append("")
                st.rerun()

            # Button to remove a BU with unique key
            if len(st.session_state.business_units) > 1 and st.button(
                "Remove Last Business Unit", key="remove_bu_btn"
            ):
                st.session_state.business_units.pop()
                st.rerun()

            # Only update session state if we've processed all existing BUs
            if len(new_business_units) == len(business_units):
                st.session_state.business_units = new_business_units

        # Environment input (if environment level is included)
        if include_env_level:
            step_number = "5" if include_bu_level else "4"
            st.subheader(f"Step {step_number}: Define Environments")
            st.markdown("Enter the names of your environments (e.g., prod, dev, qa).")

            # Get existing environments
            environments = st.session_state.environments.copy()

            # Create a column layout for environment input
            env_cols = st.columns(3)

            # Display existing environments
            new_environments = []
            for i in range(len(environments)):
                with env_cols[i % 3]:
                    env_key = f"env_{i}"
                    env_input = st.text_input(
                        f"Environment {i+1}", value=environments[i], key=env_key
                    )
                    if env_input.strip():
                        new_environments.append(env_input.strip())

            # Button to add more environments with unique key
            if st.button("Add Another Environment", key="add_env_btn"):
                st.session_state.environments.append("")
                st.rerun()

            # Button to remove an environment with unique key
            if len(st.session_state.environments) > 1 and st.button(
                "Remove Last Environment", key="remove_env_btn"
            ):
                st.session_state.environments.pop()
                st.rerun()

            # Only update session state if we've processed all existing environments
            if len(new_environments) == len(environments):
                st.session_state.environments = new_environments

        # Advanced options toggle
        st.subheader("Advanced Options")
        show_advanced = st.checkbox(
            "Show advanced configuration options", value=st.session_state.show_advanced
        )
        st.session_state.show_advanced = show_advanced

        # Default values
        env_prefix_target = st.session_state.env_prefix_target
        reserved_strategy = st.session_state.reserved_strategy
        reserved_percentage = st.session_state.reserved_percentage

        if show_advanced:
            adv_col1, adv_col2 = st.columns(2)

            with adv_col1:
                st.write("**Target Environment Prefix Length**")
                env_prefix_target = st.slider(
                    "Target prefix length for smallest subnet (environment)",
                    min_value=16,
                    max_value=24,
                    value=st.session_state.env_prefix_target,
                    help="Higher values create smaller subnets. /18 is recommended.",
                )
                st.session_state.env_prefix_target = env_prefix_target

            with adv_col2:
                st.write("**Reserved Space Strategy**")
                reserved_strategy = st.radio(
                    "Choose how reserved space is allocated",
                    ["Half of subnet", "Custom percentage"],
                    index=(
                        0
                        if st.session_state.reserved_strategy == "Half of subnet"
                        else 1
                    ),
                )
                st.session_state.reserved_strategy = reserved_strategy

                if reserved_strategy == "Custom percentage":
                    reserved_percentage = st.slider(
                        "Percentage of subnet to reserve",
                        min_value=10,
                        max_value=50,
                        value=st.session_state.reserved_percentage,
                        help="Percentage of each subnet to reserve for future use",
                    )
                    st.session_state.reserved_percentage = reserved_percentage

        # Calculate button
        calculate_section = st.container()

        with calculate_section:
            st.subheader("Generate Configuration")

            calculate_col1, calculate_col2 = st.columns([3, 1])

            with calculate_col1:
                if st.button("Calculate IPAM Configuration"):
                    # Validate inputs
                    business_units = (
                        st.session_state.business_units
                        if include_bu_level
                        else ["Default"]
                    )
                    environments = (
                        st.session_state.environments
                        if include_env_level
                        else ["Default"]
                    )

                    is_valid, error_message = ipam_logic.validate_inputs(
                        top_cidr,
                        selected_regions,
                        business_units,
                        environments,
                        include_bu_level,
                        include_env_level,
                    )

                    if not is_valid:
                        st.error(f"Configuration Error: {error_message}")
                    else:
                        # Show calculation in progress
                        with st.spinner("Calculating IPAM configuration..."):
                            # Add a small delay to show the spinner
                            time.sleep(1)

                            try:
                                # Calculate CIDR allocations
                                cidr_allocations = (
                                    ipam_logic.calculate_cidr_allocations(
                                        top_cidr,
                                        selected_regions,
                                        business_units if include_bu_level else None,
                                        environments if include_env_level else None,
                                        include_bu_level,
                                        include_env_level,
                                        primary_region,
                                        region_order=None,
                                        bu_order=None,
                                        env_order=None,
                                        environment_prefix_target=env_prefix_target,
                                        reserved_strategy=reserved_strategy,
                                        reserved_percentage=reserved_percentage,
                                    )
                                )

                                # Generate resource names
                                resource_names = ipam_logic.generate_resource_names(
                                    top_cidr,
                                    selected_regions,
                                    business_units if include_bu_level else None,
                                    environments if include_env_level else None,
                                    include_bu_level,
                                    include_env_level,
                                )

                                # Generate Terraform output
                                terraform_output = ipam_logic.generate_terraform_output(
                                    cidr_allocations,
                                    resource_names,
                                    include_bu_level,
                                    include_env_level,
                                )

                                # Generate Terraform module modifications if needed
                                terraform_module_modifications = (
                                    ipam_logic.get_modified_terraform_module(
                                        include_bu_level, include_env_level
                                    )
                                )

                                # Store results in session state
                                st.session_state.cidr_allocations = cidr_allocations
                                st.session_state.resource_names = resource_names
                                st.session_state.terraform_output = terraform_output
                                st.session_state.terraform_module_modifications = (
                                    terraform_module_modifications
                                )
                                st.session_state.calculation_complete = True

                                st.success(
                                    "IPAM configuration generated successfully! Proceed to the 'Organization', 'Visualization' and 'Terraform Output' tabs."
                                )
                            except Exception as e:
                                st.error(
                                    f"Error generating IPAM configuration: {str(e)}"
                                )

            with calculate_col2:
                if st.session_state.calculation_complete:
                    st.success("✅ Calculation Complete")

    with tab2:
        # Organization of allocations
        st.header("IPAM Pool Order Organization")

        if not st.session_state.calculation_complete:
            st.info(
                "Please calculate the IPAM configuration in the 'Configuration' tab first."
            )
        else:
            st.markdown(
                """
            In this tab, you can organize the order of CIDR allocations for Regions, Business Units, and Environments.
            The order you specify will affect how CIDR blocks are allocated in each level of the hierarchy.
            """
            )

            # Region order
            st.subheader("Region Order")
            st.write(
                "Organize Regions in accordance with desired CIDR allocation strategy."
            )

            regions = st.session_state.selected_regions

            # Initialize region order if needed
            if "region_order" not in st.session_state:
                st.session_state.region_order = regions.copy()

            # Ensure region order contains all selected regions
            for region in regions:
                if region not in st.session_state.region_order:
                    st.session_state.region_order.append(region)

            # Remove any regions that are no longer selected
            st.session_state.region_order = [
                r for r in st.session_state.region_order if r in regions
            ]

            # Create columns for the regions
            region_cols = st.columns(min(len(regions), 4))

            # Create interface for region reorganization
            for i, region in enumerate(st.session_state.region_order):
                with region_cols[i % len(region_cols)]:
                    display_name = utils.get_region_display_name(region)
                    st.write(f"**{i+1}. {display_name}**")

                    if i > 0:
                        if st.button(f"↑ {region}", key=f"region_{region}_up"):
                            # Move region up
                            idx = st.session_state.region_order.index(region)
                            (
                                st.session_state.region_order[idx],
                                st.session_state.region_order[idx - 1],
                            ) = (
                                st.session_state.region_order[idx - 1],
                                st.session_state.region_order[idx],
                            )
                            st.rerun()

                    if i < len(st.session_state.region_order) - 1:
                        if st.button(f"↓ {region}", key=f"region_{region}_down"):
                            # Move region down
                            idx = st.session_state.region_order.index(region)
                            (
                                st.session_state.region_order[idx],
                                st.session_state.region_order[idx + 1],
                            ) = (
                                st.session_state.region_order[idx + 1],
                                st.session_state.region_order[idx],
                            )
                            st.rerun()

            # Business Unit order (if BU level is included)
            if st.session_state.include_bu_level:
                st.subheader("Business Unit Order")
                st.write(
                    "Organize Business Units in accordance with desired CIDR allocation strategy (strategy repeats in each Regional Pool)."
                )

                business_units = st.session_state.business_units

                # Initialize BU order if needed
                if "bu_order" not in st.session_state:
                    st.session_state.bu_order = business_units.copy()

                # Ensure BU order contains all business units
                for bu in business_units:
                    if bu not in st.session_state.bu_order:
                        st.session_state.bu_order.append(bu)

                # Remove any BUs that are no longer defined
                st.session_state.bu_order = [
                    bu for bu in st.session_state.bu_order if bu in business_units
                ]

                # Create columns for the BUs
                bu_cols = st.columns(min(len(business_units), 4))

                # Create interface for BU reorganization
                for i, bu in enumerate(st.session_state.bu_order):
                    with bu_cols[i % len(bu_cols)]:
                        st.write(f"**{i+1}. {bu}**")

                        if i > 0:
                            if st.button(f"↑ {bu}", key=f"bu_{bu}_up"):
                                # Move BU up
                                idx = st.session_state.bu_order.index(bu)
                                (
                                    st.session_state.bu_order[idx],
                                    st.session_state.bu_order[idx - 1],
                                ) = (
                                    st.session_state.bu_order[idx - 1],
                                    st.session_state.bu_order[idx],
                                )
                                st.rerun()

                        if i < len(st.session_state.bu_order) - 1:
                            if st.button(f"↓ {bu}", key=f"bu_{bu}_down"):
                                # Move BU down
                                idx = st.session_state.bu_order.index(bu)
                                (
                                    st.session_state.bu_order[idx],
                                    st.session_state.bu_order[idx + 1],
                                ) = (
                                    st.session_state.bu_order[idx + 1],
                                    st.session_state.bu_order[idx],
                                )
                                st.rerun()

            # Environment order (if environment level is included)
            if st.session_state.include_env_level:
                st.subheader("Environment Order")
                st.write(
                    "Organize Environments in accordance with desired CIDR allocation strategy (strategy repeats in each BU Pool)."
                )

                environments = st.session_state.environments

                # Initialize environment order if needed
                if "env_order" not in st.session_state:
                    st.session_state.env_order = environments.copy()

                # Ensure environment order contains all environments
                for env in environments:
                    if env not in st.session_state.env_order:
                        st.session_state.env_order.append(env)

                # Remove any environments that are no longer defined
                st.session_state.env_order = [
                    env for env in st.session_state.env_order if env in environments
                ]

                # Create columns for the environments
                env_cols = st.columns(min(len(environments), 4))

                # Create interface for environment reorganization
                for i, env in enumerate(st.session_state.env_order):
                    with env_cols[i % len(env_cols)]:
                        st.write(f"**{i+1}. {env}**")

                        if i > 0:
                            if st.button(f"↑ {env}", key=f"env_{env}_up"):
                                # Move environment up
                                idx = st.session_state.env_order.index(env)
                                (
                                    st.session_state.env_order[idx],
                                    st.session_state.env_order[idx - 1],
                                ) = (
                                    st.session_state.env_order[idx - 1],
                                    st.session_state.env_order[idx],
                                )
                                st.rerun()

                        if i < len(st.session_state.env_order) - 1:
                            if st.button(f"↓ {env}", key=f"env_{env}_down"):
                                # Move environment down
                                idx = st.session_state.env_order.index(env)
                                (
                                    st.session_state.env_order[idx],
                                    st.session_state.env_order[idx + 1],
                                ) = (
                                    st.session_state.env_order[idx + 1],
                                    st.session_state.env_order[idx],
                                )
                                st.rerun()

            # Recalculate button
            if st.button("Recalculate with New Order"):
                with st.spinner("Recalculating IPAM configuration..."):
                    # Add a small delay to show the spinner
                    time.sleep(1)

                    try:
                        # Get configuration parameters
                        top_cidr = st.session_state.cidr_allocations["top_cidr"][0]
                        regions = st.session_state.selected_regions
                        primary_region = st.session_state.primary_region
                        business_units = (
                            st.session_state.business_units
                            if st.session_state.include_bu_level
                            else ["Default"]
                        )
                        environments = (
                            st.session_state.environments
                            if st.session_state.include_env_level
                            else ["Default"]
                        )
                        include_bu_level = st.session_state.include_bu_level
                        include_env_level = st.session_state.include_env_level
                        reserved_strategy = st.session_state.reserved_strategy
                        reserved_percentage = st.session_state.reserved_percentage
                        env_prefix_target = st.session_state.env_prefix_target

                        # Get ordering
                        region_order = st.session_state.region_order
                        bu_order = (
                            st.session_state.bu_order
                            if "bu_order" in st.session_state
                            else business_units
                        )
                        env_order = (
                            st.session_state.env_order
                            if "env_order" in st.session_state
                            else environments
                        )

                        # Calculate CIDR allocations with new order
                        cidr_allocations = ipam_logic.calculate_cidr_allocations(
                            top_cidr,
                            regions,
                            business_units if include_bu_level else None,
                            environments if include_env_level else None,
                            include_bu_level,
                            include_env_level,
                            primary_region,
                            region_order,
                            bu_order,
                            env_order,
                            environment_prefix_target=env_prefix_target,
                            reserved_strategy=reserved_strategy,
                            reserved_percentage=reserved_percentage,
                        )

                        # Generate resource names
                        resource_names = ipam_logic.generate_resource_names(
                            top_cidr,
                            regions,
                            business_units if include_bu_level else None,
                            environments if include_env_level else None,
                            include_bu_level,
                            include_env_level,
                        )

                        # Generate Terraform output
                        terraform_output = ipam_logic.generate_terraform_output(
                            cidr_allocations,
                            resource_names,
                            include_bu_level,
                            include_env_level,
                        )

                        # Store results in session state
                        st.session_state.cidr_allocations = cidr_allocations
                        st.session_state.resource_names = resource_names
                        st.session_state.terraform_output = terraform_output

                        st.success("IPAM configuration recalculated successfully!")
                    except Exception as e:
                        st.error(f"Error recalculating IPAM configuration: {str(e)}")

    with tab3:
        # Visualization of the calculated IPAM structure
        st.header("IPAM Visualization")

        if not st.session_state.calculation_complete:
            st.info(
                "Please calculate the IPAM configuration in the 'Configuration' tab first."
            )
        else:
            # Visualize the network structure
            utils.visualize_network_structure(st.session_state.cidr_allocations)

            # Display the CIDR hierarchy
            utils.display_cidr_hierarchy(st.session_state.cidr_allocations)

    with tab4:
        # Terraform output
        st.header("Terraform Output")

        if not st.session_state.calculation_complete:
            st.info(
                "Please calculate the IPAM configuration in the 'Configuration' tab first."
            )
        else:
            st.subheader("Generated Terraform Configuration")
            st.markdown(
                """
            The following configuration can be copied to a `terraform.tfvars` file to use with the IPAM Terraform module. You may also directly download this as your `terraform.tfvars` file at the bottom of this page.
            """
            )

            # Display the terraform output in a code block
            st.code(st.session_state.terraform_output, language="hcl")

            # Add a download button
            st.download_button(
                label="Download terraform.tfvars",
                data=st.session_state.terraform_output,
                file_name="terraform.tfvars",
                mime="text/plain",
            )

            # Show Terraform module modifications if necessary
            if st.session_state.terraform_module_modifications:
                st.subheader("Required Terraform Module Modifications")
                st.markdown(
                    """
                Due to the changes in hierarchy levels, you'll need to modify your Terraform module.
                Below are the recommended modifications to your Terraform code:
                """
                )

                st.code(st.session_state.terraform_module_modifications, language="hcl")

                st.download_button(
                    label="Download Module Modifications",
                    data=st.session_state.terraform_module_modifications,
                    file_name="ipam_module_modifications.tf",
                    mime="text/plain",
                )

            st.success("👆 Copy this configuration or download it as terraform.tfvars")

    # Footer
    st.markdown("---")
    st.markdown("AWS IPAM Configurator - Sample Code")


if __name__ == "__main__":
    main()
