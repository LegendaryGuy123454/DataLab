
import io

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DataLab | Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 DataLab")
st.caption("Upload, explore, visualize, and understand your data.")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

@st.cache_data(show_spinner=False)
def load_data(file_bytes, file_name, sheet_name=None):
    """Load a CSV or Excel file into a Pandas DataFrame."""
    buffer = io.BytesIO(file_bytes)

    if file_name.lower().endswith(".csv"):
        return pd.read_csv(buffer)

    return pd.read_excel(buffer, sheet_name=sheet_name)


def get_numeric_columns(data):
    """Return numeric columns."""
    return data.select_dtypes(include="number").columns.tolist()


def get_categorical_columns(data):
    """Return categorical columns."""
    return data.select_dtypes(
        include=["object", "category", "bool", "string"]
    ).columns.tolist()


def create_sample_data():
    """Create a sample sales dataset for testing."""
    return pd.DataFrame(
        {
            "Date": pd.date_range(
                start="2026-01-01",
                periods=60,
                freq="D",
            ),
            "Region": ["North", "South", "East", "West"] * 15,
            "Product": ["Laptop", "Phone", "Tablet"] * 20,
            "Sales": [
                1200, 850, 450, 700, 1500,
                920, 620, 1100, 780, 500,
            ] * 6,
            "Quantity": [
                3, 5, 2, 4, 6,
                3, 2, 5, 4, 2,
            ] * 6,
        }
    )


# ============================================================
# SIDEBAR: FILE UPLOAD
# ============================================================

with st.sidebar:
    st.header("📁 Your dataset")

    uploaded_file = st.file_uploader(
        "Upload a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload a CSV or Excel file to analyse your own data.",
    )

    st.caption("Or load sample data to explore the dashboard.")

    if st.button("Load sample sales data", use_container_width=True):
        st.session_state["sample_data"] = create_sample_data()
        st.session_state["use_sample_data"] = True
        st.rerun()

    if st.button("Return to welcome screen", use_container_width=True):
        st.session_state.pop("sample_data", None)
        st.session_state["use_sample_data"] = False
        st.rerun()


# ============================================================
# WELCOME SCREEN
# ============================================================

use_sample_data = (
    st.session_state.get("use_sample_data", False)
    and "sample_data" in st.session_state
)

if uploaded_file is None and not use_sample_data:
    st.subheader("Welcome to DataLab")

    st.write(
        "Turn raw data into useful insights using interactive charts, "
        "filters, summary statistics, and downloadable reports."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Data inspection", "Preview")

    with col2:
        st.metric("Visualizations", "Interactive")

    with col3:
        st.metric("Exports", "CSV")

    st.markdown("### Getting started")
    st.write(
        "1. Upload a CSV or Excel file using the sidebar, or\n"
        "2. Click **Load sample sales data** to test the dashboard."
    )

    st.info(
        "No dataset is loaded yet. Use the sidebar to upload a file "
        "or load the sample dataset."
    )

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith((".xlsx", ".xls")):
            excel_file = pd.ExcelFile(
                io.BytesIO(uploaded_file.getvalue())
            )

            if not excel_file.sheet_names:
                st.error("The Excel file contains no worksheets.")
                st.stop()

            with st.sidebar:
                sheet_name = st.selectbox(
                    "Choose worksheet",
                    excel_file.sheet_names,
                )

            df = load_data(
                uploaded_file.getvalue(),
                uploaded_file.name,
                sheet_name,
            )

        else:
            df = load_data(
                uploaded_file.getvalue(),
                uploaded_file.name,
            )

        st.session_state["use_sample_data"] = False

    except Exception as error:
        st.error(f"Could not read the uploaded file: {error}")
        st.info(
            "Check that the file is valid and is not password-protected."
        )
        st.stop()

else:
    df = st.session_state["sample_data"].copy()


if df.empty:
    st.warning("This dataset contains no data rows.")
    st.stop()

if len(df.columns) == 0:
    st.error("This dataset contains no columns.")
    st.stop()


# Keep the original dataset unchanged.
original_df = df.copy()

if use_sample_data and uploaded_file is None:
    st.success("Sample sales data loaded successfully.")

elif uploaded_file is not None:
    st.success(f"Loaded file: {uploaded_file.name}")


# ============================================================
# SIDEBAR: DATA FILTERS
# ============================================================

with st.sidebar:
    st.divider()
    st.header("🔎 Filter data")

    filtered_df = original_df.copy()

    categorical_columns = get_categorical_columns(original_df)
    numeric_columns = get_numeric_columns(original_df)

    # Categorical filter
    if categorical_columns:
        selected_category = st.selectbox(
            "Filter by category",
            ["None"] + categorical_columns,
        )

        if selected_category != "None":
            category_values = (
                original_df[selected_category]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            category_values = sorted(category_values)

            selected_values = st.multiselect(
                f"Select {selected_category} values",
                options=category_values,
                default=category_values,
            )

            category_mask = (
                original_df[selected_category]
                .astype(str)
                .isin(selected_values)
            )

            # Keep missing values out of categorical selections.
            filtered_df = filtered_df[category_mask]

    # Numeric range filter
    if numeric_columns:
        selected_numeric = st.selectbox(
            "Numeric range filter",
            ["None"] + numeric_columns,
        )

        if selected_numeric != "None":
            numeric_series = pd.to_numeric(
                filtered_df[selected_numeric],
                errors="coerce",
            ).dropna()

            if not numeric_series.empty:
                minimum = float(numeric_series.min())
                maximum = float(numeric_series.max())

                if minimum < maximum:
                    lower, upper = st.slider(
                        f"Range for {selected_numeric}",
                        min_value=minimum,
                        max_value=maximum,
                        value=(minimum, maximum),
                    )

                    filtered_df = filtered_df[
                        pd.to_numeric(
                            filtered_df[selected_numeric],
                            errors="coerce",
                        ).between(lower, upper)
                    ]

                else:
                    st.caption(
                        f"All available values of {selected_numeric} "
                        "are the same."
                    )

    # Search across all columns
    search_text = st.text_input("Search all columns")

    if search_text:
        search_mask = filtered_df.astype(str).apply(
            lambda column: column.str.contains(
                search_text,
                case=False,
                na=False,
                regex=False,
            )
        ).any(axis=1)

        filtered_df = filtered_df[search_mask]


# ============================================================
# DASHBOARD OVERVIEW
# ============================================================

st.divider()
st.subheader("📌 Overview")

total_rows = len(original_df)
total_columns = len(original_df.columns)
missing_cells = int(original_df.isna().sum().sum())
duplicate_rows = int(original_df.duplicated().sum())

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric("Total rows", f"{total_rows:,}")
metric2.metric("Total columns", f"{total_columns:,}")
metric3.metric("Missing cells", f"{missing_cells:,}")
metric4.metric("Duplicate rows", f"{duplicate_rows:,}")

st.caption(
    f"Showing {len(filtered_df):,} of {total_rows:,} rows after filtering."
)


# ============================================================
# MAIN DASHBOARD TABS
# ============================================================

tab_data, tab_charts, tab_analysis, tab_export = st.tabs(
    [
        "📋 Data Explorer",
        "📈 Visualizations",
        "🧠 Analysis",
        "⬇️ Export",
    ]
)


# ============================================================
# TAB 1: DATA EXPLORER
# ============================================================

with tab_data:
    st.subheader("Dataset preview")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=380,
    )

    st.subheader("Column information")

    column_info = pd.DataFrame(
        {
            "Column": original_df.columns,
            "Data type": [
                str(dtype) for dtype in original_df.dtypes
            ],
            "Non-null values": original_df.notna().sum().values,
            "Missing values": original_df.isna().sum().values,
            "Unique values": original_df.nunique(
                dropna=True
            ).values,
        }
    )

    st.dataframe(
        column_info,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("View descriptive statistics"):
        st.dataframe(
            original_df.describe(include="all").transpose(),
            use_container_width=True,
        )


# ============================================================
# TAB 2: INTERACTIVE VISUALIZATIONS
# ============================================================

with tab_charts:
    st.subheader("Build your own chart")

    chart_types = [
        "Bar chart",
        "Line chart",
        "Scatter plot",
        "Histogram",
        "Box plot",
        "Pie chart",
        "Correlation heatmap",
    ]

    chart_type = st.selectbox(
        "Chart type",
        chart_types,
    )

    available_columns = filtered_df.columns.tolist()
    numeric_columns = get_numeric_columns(filtered_df)
    categorical_columns = get_categorical_columns(filtered_df)

    if filtered_df.empty:
        st.warning(
            "No rows match the current filters. Adjust your filters "
            "to generate charts."
        )

    elif chart_type == "Correlation heatmap":
        if len(numeric_columns) < 2:
            st.warning(
                "A correlation heatmap requires at least two numeric columns."
            )
        else:
            correlation = filtered_df[numeric_columns].corr(
                numeric_only=True
            )

            fig = px.imshow(
                correlation,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                title="Correlation between numeric columns",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    elif chart_type == "Histogram":
        if not numeric_columns:
            st.warning("A histogram requires a numeric column.")
        else:
            x_column = st.selectbox(
                "Column to analyse",
                numeric_columns,
            )

            bins = st.slider(
                "Number of bins",
                min_value=5,
                max_value=100,
                value=25,
            )

            fig = px.histogram(
                filtered_df,
                x=x_column,
                nbins=bins,
                title=f"Distribution of {x_column}",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    elif chart_type == "Pie chart":
        if not categorical_columns:
            st.warning(
                "A pie chart requires a categorical column."
            )
        else:
            category = st.selectbox(
                "Category",
                categorical_columns,
            )

            counts = (
                filtered_df[category]
                .fillna("Missing")
                .astype(str)
                .value_counts()
                .head(20)
                .rename_axis(category)
                .reset_index(name="Count")
            )

            fig = px.pie(
                counts,
                names=category,
                values="Count",
                title=f"Distribution of {category} (top 20)",
                hole=0.3,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    elif chart_type == "Box plot":
        if not numeric_columns:
            st.warning("A box plot requires a numeric column.")
        else:
            y_column = st.selectbox(
                "Numeric column",
                numeric_columns,
            )

            group_options = ["None"] + available_columns

            group_column = st.selectbox(
                "Group by (optional)",
                group_options,
            )

            fig = px.box(
                filtered_df,
                x=(
                    None
                    if group_column == "None"
                    else group_column
                ),
                y=y_column,
                title=f"Distribution of {y_column}",
                points="outliers",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    else:
        if not available_columns:
            st.warning("There are no columns to plot.")

        elif chart_type == "Scatter plot" and len(numeric_columns) < 2:
            st.warning(
                "A scatter plot requires at least two numeric columns."
            )

        elif not numeric_columns:
            st.warning(
                "This chart requires at least one numeric column."
            )

        else:
            x_column = st.selectbox(
                "X-axis",
                available_columns,
            )

            if chart_type == "Scatter plot":
                y_options = [
                    column
                    for column in numeric_columns
                    if column != x_column
                ]

                if not y_options:
                    y_options = numeric_columns
            else:
                y_options = numeric_columns

            y_column = st.selectbox(
                "Y-axis",
                y_options,
            )

            aggregation = st.selectbox(
                "Aggregation",
                ["None", "Sum", "Mean", "Count", "Median"],
                disabled=(chart_type == "Scatter plot"),
            )

            plot_df = filtered_df.copy()
            y_to_plot = y_column

            if aggregation != "None":
                if aggregation == "Count":
                    plot_df = (
                        filtered_df.groupby(
                            x_column,
                            dropna=False,
                        )[y_column]
                        .count()
                        .reset_index(name="Count")
                    )

                    y_to_plot = "Count"

                else:
                    agg_function = {
                        "Sum": "sum",
                        "Mean": "mean",
                        "Median": "median",
                    }[aggregation]

                    plot_df = (
                        filtered_df.groupby(
                            x_column,
                            dropna=False,
                        )[y_column]
                        .agg(agg_function)
                        .reset_index()
                    )

            if chart_type == "Bar chart":
                fig = px.bar(
                    plot_df,
                    x=x_column,
                    y=y_to_plot,
                    title=(
                        f"{aggregation if aggregation != 'None' else 'Values'} "
                        f"of {y_column} by {x_column}"
                    ),
                )

            elif chart_type == "Line chart":
                fig = px.line(
                    plot_df,
                    x=x_column,
                    y=y_to_plot,
                    markers=True,
                    title=f"{y_column} by {x_column}",
                )

            else:
                fig = px.scatter(
                    plot_df,
                    x=x_column,
                    y=y_to_plot,
                    title=f"{y_column} vs {x_column}",
                )

            fig.update_layout(
                xaxis_title=x_column,
                yaxis_title=y_to_plot,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    st.caption(
        "Hover over charts to inspect values. Use the chart toolbar "
        "to zoom, pan, or save a chart as an image."
    )


# ============================================================
# TAB 3: AUTOMATIC ANALYSIS
# ============================================================

with tab_analysis:
    st.subheader("Automatic insights")

    st.markdown("#### Data quality")

    quality = pd.DataFrame(
        {
            "Missing values": original_df.isna().sum(),
            "Missing (%)": (
                original_df.isna().mean() * 100
            ).round(2),
            "Unique values": original_df.nunique(
                dropna=True
            ),
        }
    )

    st.dataframe(
        quality,
        use_container_width=True,
    )

    if missing_cells:
        st.warning(
            f"The dataset contains {missing_cells:,} missing cells. "
            "Check these before drawing conclusions."
        )
    else:
        st.success("No missing cells were found.")

    if duplicate_rows:
        st.info(
            f"Found {duplicate_rows:,} duplicate rows."
        )

    st.markdown("#### Numeric summaries")

    numeric_columns = get_numeric_columns(filtered_df)

    if numeric_columns:
        st.dataframe(
            filtered_df[numeric_columns].describe().transpose(),
            use_container_width=True,
        )

        if len(numeric_columns) >= 2:
            st.markdown("#### Strongest numeric correlations")

            corr = filtered_df[numeric_columns].corr(
                numeric_only=True
            )

            pairs = []

            for i in range(len(corr.columns)):
                for j in range(i + 1, len(corr.columns)):
                    value = corr.iloc[i, j]

                    if pd.notna(value):
                        pairs.append(
                            {
                                "Column 1": corr.columns[i],
                                "Column 2": corr.columns[j],
                                "Correlation": value,
                                "Absolute correlation": abs(value),
                            }
                        )

            if pairs:
                pairs_df = pd.DataFrame(pairs)

                pairs_df = pairs_df.sort_values(
                    "Absolute correlation",
                    ascending=False,
                )

                st.dataframe(
                    pairs_df.drop(
                        columns=["Absolute correlation"]
                    ).head(10),
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Correlation measures association, not causation."
                )

    else:
        st.info("No numeric columns were detected in the filtered data.")


# ============================================================
# TAB 4: EXPORT
# ============================================================

with tab_export:
    st.subheader("Download your results")

    st.write(
        "Export the currently filtered dataset or download a report "
        "about the original dataset's structure and data quality."
    )

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download filtered data (CSV)",
        data=csv_data,
        file_name="filtered_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

    report = pd.DataFrame(
        {
            "Column": original_df.columns,
            "Data type": [
                str(dtype) for dtype in original_df.dtypes
            ],
            "Non-null values": original_df.notna().sum().values,
            "Missing values": original_df.isna().sum().values,
            "Unique values": original_df.nunique(
                dropna=True
            ).values,
        }
    )

    report_csv = report.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="⬇️ Download data quality report (CSV)",
        data=report_csv,
        file_name="data_quality_report.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("#### Current filtered dataset")

    col1, col2 = st.columns(2)

    col1.metric("Rows", f"{len(filtered_df):,}")
    col2.metric("Columns", f"{len(filtered_df.columns):,}")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "DataLab | Built with Python, Pandas, Plotly, and Streamlit"
)
