import ipaddress
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


def display_cidr_hierarchy(cidr_allocations: Dict[str, Any]) -> None:
    """
    Display a visual representation of the CIDR hierarchy using tables.

    Args:
        cidr_allocations: Dictionary with calculated CIDR allocations
    """
    # Create a dataframe for the top-level CIDR
    top_df = pd.DataFrame(
        {
            "Level": ["Top"],
            "CIDR": cidr_allocations["top_cidr"],
            "IP Range": [
                f"{ipaddress.IPv4Network(cidr_allocations['top_cidr'][0]).network_address} - "
                f"{ipaddress.IPv4Network(cidr_allocations['top_cidr'][0]).broadcast_address}"
            ],
            "Usable IPs": [
                format_ip_count(
                    ipaddress.IPv4Network(cidr_allocations["top_cidr"][0]).num_addresses
                )
            ],
        }
    )

    st.subheader("CIDR Hierarchy")
    st.write("Top-Level Pool")
    st.dataframe(top_df, hide_index=True)

    # Check if regional CIDRs exist
    if "regional_cidrs" in cidr_allocations and cidr_allocations["regional_cidrs"]:
        # Create a dataframe for the regional CIDRs
        regional_data = []
        for region, data in cidr_allocations["regional_cidrs"].items():
            cidr = data["cidr"][0]
            network = ipaddress.IPv4Network(cidr)
            regional_data.append(
                {
                    "Region": region,
                    "CIDR": cidr,
                    "IP Range": f"{network.network_address} - {network.broadcast_address}",
                    "Usable IPs": format_ip_count(network.num_addresses),
                }
            )

        regional_df = pd.DataFrame(regional_data)

        st.write("Regional Pools")
        st.dataframe(regional_df, hide_index=True)

    # Check if BU CIDRs exist
    if "bu_cidrs" in cidr_allocations and cidr_allocations["bu_cidrs"]:
        # Create dataframes for each region's BU CIDRs
        st.write("Business Unit Pools")
        for region, bus in cidr_allocations["bu_cidrs"].items():
            bu_data = []
            for bu, bu_info in bus.items():
                cidr = bu_info["cidr"][0]
                network = ipaddress.IPv4Network(cidr)
                bu_data.append(
                    {
                        "Business Unit": bu,
                        "CIDR": cidr,
                        "IP Range": f"{network.network_address} - {network.broadcast_address}",
                        "Usable IPs": format_ip_count(network.num_addresses),
                    }
                )

            bu_df = pd.DataFrame(bu_data)
            st.write(f"Region: {region}")
            st.dataframe(bu_df, hide_index=True)

    # Check if environment CIDRs exist
    if "env_cidrs" in cidr_allocations and cidr_allocations["env_cidrs"]:
        # Create dataframes for each region's environment CIDRs
        st.write("Environment Pools")
        for region, bus in cidr_allocations["env_cidrs"].items():
            st.write(f"Region: {region}")

            for bu, envs in bus.items():
                env_data = []
                for env, env_info in envs.items():
                    cidr = env_info["cidr"][0]
                    reserved = env_info.get("reserved_cidr", "")
                    network = ipaddress.IPv4Network(cidr)
                    env_data.append(
                        {
                            "Environment": env,
                            "CIDR": cidr,
                            "Reserved CIDR": reserved,
                            "IP Range": f"{network.network_address} - {network.broadcast_address}",
                            "Usable IPs": format_ip_count(network.num_addresses),
                        }
                    )

                env_df = pd.DataFrame(env_data)
                st.write(f"Business Unit: {bu}")
                st.dataframe(env_df, hide_index=True)


def format_ip_count(count: int) -> str:
    """Format an IP address count with commas and proper suffix."""
    if count >= 1000000:
        return f"{count/1000000:.2f}M"
    elif count >= 1000:
        return f"{count/1000:.2f}K"
    else:
        return f"{count:,}"


def visualize_network_structure(cidr_allocations: Dict[str, Any]) -> None:
    """
    Create a hierarchical visualization of the network structure using Plotly.

    Args:
        cidr_allocations: Dictionary with calculated CIDR allocations
    """
    # Top-level stats
    top_cidr = cidr_allocations["top_cidr"][0]
    network = ipaddress.IPv4Network(top_cidr)
    total_ips = network.num_addresses

    # Calculate IP allocations at each level
    summary_stats = calculate_allocation_stats(cidr_allocations)

    st.subheader("IP Address Allocation Overview")

    # Display IP utilization metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total IP Space", format_ip_count(total_ips))
    with col2:
        allocated_ips = (
            total_ips
            if "regional_cidrs" not in cidr_allocations
            else sum(
                ipaddress.IPv4Network(data["cidr"][0]).num_addresses
                for region, data in cidr_allocations["regional_cidrs"].items()
            )
        )
        st.metric("Allocated IPs", format_ip_count(allocated_ips))
    with col3:
        utilization = (
            100 if allocated_ips == total_ips else (allocated_ips / total_ips) * 100
        )
        st.metric("Utilization", f"{utilization:.1f}%")

    # Create hierarchy visualization
    fig = create_hierarchy_visualization(cidr_allocations)
    st.plotly_chart(fig, use_container_width=True)

    # Create a summary table
    st.subheader("Allocation Summary")
    summary_df = pd.DataFrame(summary_stats)
    st.table(summary_df)


def calculate_allocation_stats(cidr_allocations: Dict[str, Any]) -> pd.DataFrame:
    """Calculate allocation statistics at each level of the hierarchy."""
    top_cidr = cidr_allocations["top_cidr"][0]
    top_network = ipaddress.IPv4Network(top_cidr)
    top_ips = top_network.num_addresses

    stats = {
        "Pool Level": ["Top"],
        "Total IPs": [format_ip_count(top_ips)],
        "Allocation Count": [1],
        "Average Size": [format_ip_count(top_ips)],
    }

    # Regional stats
    if "regional_cidrs" in cidr_allocations and cidr_allocations["regional_cidrs"]:
        regional_ips = sum(
            ipaddress.IPv4Network(data["cidr"][0]).num_addresses
            for region, data in cidr_allocations["regional_cidrs"].items()
        )
        regional_count = len(cidr_allocations["regional_cidrs"])
        stats["Pool Level"].append("Regional")
        stats["Total IPs"].append(format_ip_count(regional_ips))
        stats["Allocation Count"].append(regional_count)
        stats["Average Size"].append(format_ip_count(regional_ips // regional_count))

    # BU stats
    if "bu_cidrs" in cidr_allocations and cidr_allocations["bu_cidrs"]:
        bu_count = 0
        bu_ips = 0
        for region, bus in cidr_allocations["bu_cidrs"].items():
            for bu, bu_info in bus.items():
                bu_count += 1
                bu_ips += ipaddress.IPv4Network(bu_info["cidr"][0]).num_addresses

        stats["Pool Level"].append("Business Unit")
        stats["Total IPs"].append(format_ip_count(bu_ips))
        stats["Allocation Count"].append(bu_count)
        stats["Average Size"].append(
            format_ip_count(bu_ips // bu_count if bu_count > 0 else 0)
        )

    # Environment stats
    if "env_cidrs" in cidr_allocations and cidr_allocations["env_cidrs"]:
        env_count = 0
        env_ips = 0
        for region, bus in cidr_allocations["env_cidrs"].items():
            for bu, envs in bus.items():
                for env, env_info in envs.items():
                    env_count += 1
                    env_ips += ipaddress.IPv4Network(env_info["cidr"][0]).num_addresses

        stats["Pool Level"].append("Environment")
        stats["Total IPs"].append(format_ip_count(env_ips))
        stats["Allocation Count"].append(env_count)
        stats["Average Size"].append(
            format_ip_count(env_ips // env_count if env_count > 0 else 0)
        )

    return pd.DataFrame(stats)


def create_hierarchy_visualization(cidr_allocations: Dict[str, Any]) -> go.Figure:
    """Create a hierarchical visualization of the IP address allocations."""
    # Create labels and values for the sunburst chart
    labels = []
    parents = []
    values = []
    hover_text = []

    # Add top-level
    top_cidr = cidr_allocations["top_cidr"][0]
    top_network = ipaddress.IPv4Network(top_cidr)
    top_ips = top_network.num_addresses
    top_label = f"Top: {top_cidr}"

    labels.append(top_label)
    parents.append("")
    values.append(top_ips)
    hover_text.append(f"CIDR: {top_cidr}<br>IPs: {format_ip_count(top_ips)}")

    # Add regions if they exist
    if "regional_cidrs" in cidr_allocations and cidr_allocations["regional_cidrs"]:
        for region, data in cidr_allocations["regional_cidrs"].items():
            region_cidr = data["cidr"][0]
            region_network = ipaddress.IPv4Network(region_cidr)
            region_ips = region_network.num_addresses
            region_label = f"{region}: {region_cidr}"

            labels.append(region_label)
            parents.append(top_label)
            values.append(region_ips)
            hover_text.append(
                f"Region: {region}<br>CIDR: {region_cidr}<br>IPs: {format_ip_count(region_ips)}"
            )

    # Add BUs if they exist
    if "bu_cidrs" in cidr_allocations and cidr_allocations["bu_cidrs"]:
        for region, bus in cidr_allocations["bu_cidrs"].items():
            region_label = (
                f"{region}: {cidr_allocations['regional_cidrs'][region]['cidr'][0]}"
            )

            for bu, bu_info in bus.items():
                bu_cidr = bu_info["cidr"][0]
                bu_network = ipaddress.IPv4Network(bu_cidr)
                bu_ips = bu_network.num_addresses
                bu_label = f"{region}-{bu}: {bu_cidr}"

                labels.append(bu_label)
                parents.append(region_label)
                values.append(bu_ips)
                hover_text.append(
                    f"Region: {region}<br>BU: {bu}<br>CIDR: {bu_cidr}<br>IPs: {format_ip_count(bu_ips)}"
                )

    # Add environments if they exist
    if "env_cidrs" in cidr_allocations and cidr_allocations["env_cidrs"]:
        for region, bus in cidr_allocations["env_cidrs"].items():
            for bu, envs in bus.items():
                bu_label = f"{region}-{bu}: {cidr_allocations['bu_cidrs'][region][bu]['cidr'][0]}"

                for env, env_info in envs.items():
                    env_cidr = env_info["cidr"][0]
                    env_network = ipaddress.IPv4Network(env_cidr)
                    env_ips = env_network.num_addresses
                    env_label = f"{region}-{bu}-{env}: {env_cidr}"

                    labels.append(env_label)
                    parents.append(bu_label)
                    values.append(env_ips)
                    hover_text.append(
                        f"Region: {region}<br>BU: {bu}<br>Env: {env}<br>CIDR: {env_cidr}<br>IPs: {format_ip_count(env_ips)}"
                    )

    # Create sunburst figure
    fig = go.Figure(
        go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            hovertext=hover_text,
            hoverinfo="text",
            maxdepth=3,
        )
    )

    fig.update_layout(
        title="IP Address Hierarchy",
        margin=dict(t=30, l=0, r=0, b=0),
        height=600,
    )

    return fig


def get_ipam_regions() -> List[Dict[str, str]]:
    """Return a list of AWS regions that support IPAM with their display names."""
    return [
        {"code": "us-east-1", "name": "US East (N. Virginia)"},
        {"code": "us-east-2", "name": "US East (Ohio)"},
        {"code": "us-west-1", "name": "US West (N. California)"},
        {"code": "us-west-2", "name": "US West (Oregon)"},
        {"code": "ca-central-1", "name": "Canada (Central)"},
        {"code": "eu-north-1", "name": "EU North (Stockholm)"},
        {"code": "eu-west-1", "name": "EU West (Ireland)"},
        {"code": "eu-west-2", "name": "EU West (London)"},
        {"code": "eu-west-3", "name": "EU West (Paris)"},
        {"code": "eu-central-1", "name": "EU Central (Frankfurt)"},
        {"code": "eu-south-1", "name": "EU South (Milan)"},
        {"code": "ap-northeast-1", "name": "AP Northeast (Tokyo)"},
        {"code": "ap-northeast-2", "name": "AP Northeast (Seoul)"},
        {"code": "ap-northeast-3", "name": "AP Northeast (Osaka)"},
        {"code": "ap-southeast-1", "name": "AP Southeast (Singapore)"},
        {"code": "ap-southeast-2", "name": "AP Southeast (Sydney)"},
        {"code": "ap-south-1", "name": "AP South (Mumbai)"},
        {"code": "sa-east-1", "name": "SA East (São Paulo)"},
        {"code": "af-south-1", "name": "Africa (Cape Town)"},
        {"code": "me-south-1", "name": "Middle East (Bahrain)"},
    ]


def get_region_display_name(region_code: str) -> str:
    """Convert AWS region code to a human-readable display name."""
    regions = get_ipam_regions()
    for region in regions:
        if region["code"] == region_code:
            return region["name"]
    return region_code


def create_sortable_list(items: List[str], title: str, key_prefix: str) -> None:
    """Create a sortable list using streamlit session state."""
    if f"{key_prefix}_order" not in st.session_state:
        st.session_state[f"{key_prefix}_order"] = list(range(len(items)))

    st.write(f"### {title} Order")
    st.write("Reorganize items (first item will have first CIDR allocation)")

    # Create columns for the reordering UI
    cols = st.columns(len(items))

    for i, item_idx in enumerate(st.session_state[f"{key_prefix}_order"]):
        if item_idx < len(items):
            with cols[i]:
                item = items[item_idx]
                st.write(f"**{i+1}. {item}**")
                if i > 0:
                    if st.button(f"↑ {item}", key=f"{key_prefix}_{item}_up"):
                        # Swap with previous item
                        idx = st.session_state[f"{key_prefix}_order"].index(item_idx)
                        (
                            st.session_state[f"{key_prefix}_order"][idx],
                            st.session_state[f"{key_prefix}_order"][idx - 1],
                        ) = (
                            st.session_state[f"{key_prefix}_order"][idx - 1],
                            st.session_state[f"{key_prefix}_order"][idx],
                        )
                        st.rerun()
                if i < len(items) - 1:
                    if st.button(f"↓ {item}", key=f"{key_prefix}_{item}_down"):
                        # Swap with next item
                        idx = st.session_state[f"{key_prefix}_order"].index(item_idx)
                        (
                            st.session_state[f"{key_prefix}_order"][idx],
                            st.session_state[f"{key_prefix}_order"][idx + 1],
                        ) = (
                            st.session_state[f"{key_prefix}_order"][idx + 1],
                            st.session_state[f"{key_prefix}_order"][idx],
                        )
                        st.rerun()


def get_ordered_items(items: List[str], key_prefix: str) -> List[str]:
    """Get the items in the order specified by the user."""
    if f"{key_prefix}_order" not in st.session_state:
        return items

    ordered_indices = st.session_state[f"{key_prefix}_order"]
    if len(ordered_indices) != len(items):
        # Reset if the lengths don't match
        st.session_state[f"{key_prefix}_order"] = list(range(len(items)))
        return items

    return [items[idx] for idx in ordered_indices if idx < len(items)]
