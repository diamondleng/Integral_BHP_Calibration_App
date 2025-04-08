import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
import io

# App title
st.title("Formation-Based Calibration Visualization")

# Layout with two columns
left_col, right_col = st.columns([1, 2])

with left_col:
    st.header("Step 1: Upload Input Files")
    calib_result_file = st.file_uploader("Upload Calibration Result Excel", type=["xlsx"])
    field_data_file = st.file_uploader("Upload Calibration Field Data Excel", type=["xlsx"])
    dat_file = st.file_uploader("Upload Simulation .dat File", type=["dat"])

    if "formation_mapping" not in st.session_state:
        st.session_state["formation_mapping"] = {
            "BELL": {1, 2, 3, 4},
            "CHERRY": {7, 8, 9},
            "BRUSHY": {10, 11, 12}
        }

    formation_mapping = st.session_state["formation_mapping"]

    if calib_result_file and field_data_file and dat_file:
        if st.button("Initialize Formations"):
            st.session_state["show_formation_form"] = True

    if st.session_state.get("show_formation_form"):
        with st.expander("Define Formations by Layer Numbers", expanded=True):
            formation_inputs = {}
            max_formations = 10
            for i in range(max_formations):
                col1, col2 = st.columns(2)
                name_key = f"name_{i}"
                layers_key = f"layers_{i}"

                if name_key not in st.session_state:
                    st.session_state[name_key] = ""
                if layers_key not in st.session_state:
                    st.session_state[layers_key] = ""

                with col1:
                    name = st.text_input(f"Formation {i+1} Name", value=st.session_state[name_key], key=name_key)
                with col2:
                    layers = st.text_input(f"Formation {i+1} Layers (comma-separated)", value=st.session_state[layers_key], key=layers_key)

                if name and layers:
                    try:
                        layer_nums = set(map(int, layers.split(",")))
                        formation_inputs[name] = layer_nums
                    except ValueError:
                        st.warning(f"Invalid layer input for formation {name}")

            if st.button("Apply Formation Mapping") and formation_inputs:
                st.session_state["formation_mapping"] = formation_inputs
                st.success("Formation mapping updated. Rerun to apply.")
                st.rerun()

with right_col:
    formation_mapping = st.session_state["formation_mapping"]
    df_wells = pd.DataFrame()

    if dat_file is not None:
        lines = dat_file.read().decode("utf-8").splitlines()

        well_data = {}
        inside_well_section = False
        current_well = None

        for i, line in enumerate(lines):
            line = line.strip()

            if line.startswith("RUN"):
                inside_well_section = True
                continue

            if line.startswith("STOP"):
                inside_well_section = False
                continue

            if inside_well_section and line.startswith("WELL"):
                parts = line.split("'")
                if len(parts) > 1:
                    current_well = parts[1].strip()
                    well_data[current_well] = {"location": None, "layers": set(), "formation": set()}

            if current_well and "** UBA" in line:
                j = i + 1
                while j < len(lines) and not lines[j].startswith(("**", "LAYERXYZ")):
                    perf_parts = lines[j].split()
                    if len(perf_parts) >= 3:
                        x, y, z = int(perf_parts[0]), int(perf_parts[1]), int(perf_parts[2])
                        if well_data[current_well]["location"] is None:
                            well_data[current_well]["location"] = (x, y)
                        well_data[current_well]["layers"].add(z)

                        for formation_name, layer_set in formation_mapping.items():
                            if z in layer_set:
                                well_data[current_well]["formation"].add(formation_name)
                    j += 1

        df_wells = pd.DataFrame.from_dict(well_data, orient="index")
        df_wells["layers"] = df_wells["layers"].apply(lambda x: sorted(list(x)) if x else [])
        df_wells["formation"] = df_wells["formation"].apply(lambda x: sorted(list(x)) if x else [])

    if not df_wells.empty:
        all_formations = sorted(set([f for sublist in df_wells["formation"] for f in sublist]))
        selected_formations = st.multiselect("Select Formations of Interest", all_formations)

        if selected_formations and calib_result_file and field_data_file:
            df_wells = df_wells[df_wells["formation"].apply(lambda x: any(f in selected_formations for f in x))]

            well_pressure_df = pd.read_excel(calib_result_file, usecols=["Name", "Date", "Value"])
            field_data_raw = pd.read_excel(field_data_file)

            well_col = "API_10" if "API_10" in field_data_raw.columns else "API"
            date_col = "Injection Date" if "Injection Date" in field_data_raw.columns else "Date"
            bhp_col = "BHP_MDF_T" if "BHP_MDF_T" in field_data_raw.columns else "BHP, psi"

            injection_df_full = field_data_raw[[well_col, date_col, bhp_col]].copy()
            injection_df_full.rename(columns={well_col: "Well_Name", bhp_col: "BHP B3"}, inplace=True)
            injection_df_full["Injection Date"] = pd.to_datetime(injection_df_full[date_col])

            well_pressure_df.rename(columns={"Name": "Well_Name", "Value": "BHP Simulation"}, inplace=True)
            well_pressure_df["Date"] = pd.to_datetime(well_pressure_df["Date"])

            merged_df = pd.merge(
                well_pressure_df,
                injection_df_full,
                left_on=["Well_Name", "Date"],
                right_on=["Well_Name", "Injection Date"],
                how="inner",
            )

            merged_df.dropna(subset=["BHP Simulation", "BHP B3"], inplace=True)

            merged_df["formation"] = merged_df["Well_Name"].astype(str).map(
                lambda well: df_wells.loc[well, "formation"][0] if well in df_wells.index and df_wells.loc[well, "formation"] else None
            )

            formation_colors = {f: c for f, c in zip(all_formations, ["blue", "green", "orange", "red", "purple", "brown"])}

            def get_color(formation):
                return formation_colors.get(formation, "gray")

            merged_df["Color"] = merged_df["formation"].apply(get_color)

            rmse = np.sqrt(mean_squared_error(merged_df["BHP Simulation"], merged_df["BHP B3"]))
            merged_df["Residual"] = np.abs(merged_df["BHP Simulation"] - merged_df["BHP B3"])
            sigma = merged_df["Residual"].std()
            threshold_fixed = 1000
            within_confidence = (merged_df["Residual"] <= threshold_fixed).sum()
            fraction_within_conf = within_confidence / len(merged_df)

            st.write(f"RMSE: {rmse:.2f} psi")
            st.write(f"Fraction within ±1000 psi: {fraction_within_conf:.2%}")

            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(16, 6))
            upper_lim, lower_lim = 7000, 0

            axes[0].scatter(merged_df["BHP Simulation"], merged_df["BHP B3"], c=merged_df["Color"], alpha=0.6)
            axes[0].plot([lower_lim, upper_lim], [lower_lim, upper_lim], color="red", linestyle="--", linewidth=2)
            axes[0].plot([lower_lim, upper_lim], [lower_lim + threshold_fixed, upper_lim + threshold_fixed], color="blue", linestyle="--")
            axes[0].plot([lower_lim, upper_lim], [lower_lim - threshold_fixed, upper_lim - threshold_fixed], color="blue", linestyle="--")
            axes[0].set_xlim(lower_lim, upper_lim)
            axes[0].set_ylim(lower_lim, upper_lim)
            axes[0].set_title("Simulation vs B3 Data (Scatter Plot)")

            formation_fractions = {}
            for formation in all_formations:
                subset = merged_df[merged_df["formation"] == formation]
                if not subset.empty:
                    frac = (subset["Residual"] <= threshold_fixed).mean()
                    label = f"{formation} ({frac:.1%})"
                    axes[0].scatter([], [], color=formation_colors.get(formation, "gray"), label=label)
            axes[0].legend(title="Formation (Within ±1000 psi)")

            x_bins = np.arange(lower_lim, upper_lim, 100)
            y_bins = np.arange(lower_lim, upper_lim, 100)
            hist = axes[1].hist2d(merged_df["BHP Simulation"], merged_df["BHP B3"], bins=[x_bins, y_bins], cmap="Reds")
            axes[1].plot([lower_lim, upper_lim], [lower_lim, upper_lim], color="red", linestyle="--", linewidth=2)
            axes[1].set_xlim(lower_lim, upper_lim)
            axes[1].set_ylim(lower_lim, upper_lim)
            axes[1].set_title("Simulation vs B3 Data (Density Plot)")
            fig.colorbar(hist[3], ax=axes[1], label="Density")

            st.pyplot(fig)
