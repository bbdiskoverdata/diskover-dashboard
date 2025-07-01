import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import uuid
import sys
from PIL import Image
import plotly.io as pio
import tempfile

# Page config
st.set_page_config(page_title="Diskover Index Dashboard", layout="wide", page_icon="📁")

# Custom CSS for dark theme and button styling
st.markdown("""
<style>
  body { background-color: #2b2d31; color: #e1e1e1; font-family: 'Segoe UI', sans-serif; }
  .stApp { background-color: #2b2d31; }
  .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { color: #ffffff; }
  .stButton>button, .stDownloadButton>button { background-color: #444; color: #ffffff; font-weight: bold; border-radius: 6px; }
  .stButton>button:hover, .stDownloadButton>button:hover { background-color: #666; color: #ffffff; }
    /* Entire radio container */
  div[data-testid="stRadio"] {
    color: white !important;
  }
  /* All descendants (labels, spans, etc.) */
  div[data-testid="stRadio"] * {
    color: white !important;
  }          
</style>
""", unsafe_allow_html=True)


# Now your radio will render in white
#unit = st.radio("Select size unit", ("GB", "TB", "PB"), horizontal=True)

# Header image
try:
    logo = Image.open("Diskover_Banner.png")
    st.image(logo, use_container_width=False, width=700)
except:
    pass

# Title
st.markdown("<h1 style='color:white; font-size:32px; font-weight:700;'>Diskover File Analysis Dashboard</h1>", unsafe_allow_html=True)

# File uploader
uploaded = st.file_uploader("Upload CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    df = df.dropna(subset=["Index", "Type"])

    # Index filter
    all_indexes = df["Index"].unique().tolist()
    st.markdown("<p style='color:white; font-size:20px; font-weight:600;'>Select Indexes to View</p>", unsafe_allow_html=True)
    selected = st.multiselect(
        "Select Indexes",
        options=["(All)"] + all_indexes,
        default=["(All)"],
        label_visibility="collapsed"
    )
    if "(All)" in selected:
        view_df = df
    else:
        view_df = df[df["Index"].isin(selected)]
            # 📏 Size unit toggle

    unit = st.radio("Select size unit", ("GB", "TB", "PB"), horizontal=True)
    unit_factor = {"GB": 1/1024**3, "TB": 1/1024**4, "PB": 1/1024**5}[unit]
    size_col = f"Size ({unit})"


    # Summary header
    st.markdown("<h2 style='color:white; font-size:26px; font-weight:600;'>📊 Summary</h2>", unsafe_allow_html=True)

    # Extensions summary
        # 🧩 Extensions Summary
    ext_df = view_df[view_df["Type"] == "Top Extension"].copy()
    if not ext_df.empty:
        # Aggregate counts & raw bytes
        ext_agg = ext_df.groupby("Key").agg({
            "Count": "sum",
            "Size (Bytes)": "sum"
        }).reset_index()
        # Compute in chosen unit (GB/TB/PB)
        ext_agg[size_col] = ext_agg["Size (Bytes)"] * unit_factor

        st.markdown("#### 🧩 Top 20 Extensions by Size")

        top20 = ext_agg.sort_values("Size (Bytes)", ascending=False).head(20)
        # Create bar chart with no title, then explicitly clear any title text
        fig_ext = px.bar(
            top20,
            x="Key",
            y=size_col,
            hover_data={"Count": True, size_col: ".2f"},
            text=top20[size_col].map("{:,.2f}".format),
            labels={"Key": "Extension", size_col: f"Total Size ({unit})"},
            template="plotly_dark",
            title=None  # ensures Plotly doesn’t insert a default title
        )
        fig_ext.update_layout(
            title_text="",  # explicitly clear title area
            title_font=dict(color="white", size=22),
            font=dict(color="white", size=14),
            legend=dict(font=dict(color="white", size=14)),
            xaxis_title="Extension",
            yaxis_title=f"Total Size ({unit})",
            plot_bgcolor="#2b2d31",
            paper_bgcolor="#2b2d31",
        )
        st.plotly_chart(fig_ext, use_container_width=True)

        st.markdown("#### 🥧 File Extensions by Count")
        pie_df = ext_agg.copy()
        pie_df["Percent"] = pie_df["Count"] / pie_df["Count"].sum()
        pie_df = pie_df[pie_df["Percent"] >= 0.01]
        fig_pie = px.pie(
            pie_df,
            names="Key",
            values="Count",
            template="plotly_dark",
            title=""
        )
        fig_pie.update_layout(
            font=dict(color="white", size=14),
            legend=dict(font=dict(color="white", size=14)),
            plot_bgcolor="#2b2d31",
            paper_bgcolor="#2b2d31",
        )
        st.plotly_chart(fig_pie, use_container_width=True)


    # Hot/Warm/Cold summary
    tier_df = view_df[view_df["Type"].str.contains("Summary", na=False)].copy()
    tier_df["Field"] = tier_df["Type"].str.extract(r"(MTIME|ATIME)")
    agg_tier = tier_df.groupby(["Key", "Field"]).agg({"Count": "sum", "Size (Bytes)": "sum"}).reset_index()
    agg_tier["Size (GB)"] = agg_tier["Size (Bytes)"] / 1024**3
    agg_tier["Key"] = agg_tier["Key"].str.title()
    agg_tier = agg_tier[agg_tier["Key"].isin(["Hot", "Warm", "Cold"])]
    agg_tier["Key"] = pd.Categorical(agg_tier["Key"], categories=["Hot", "Warm", "Cold"], ordered=True)
        # compute in selected unit (unit, unit_factor defined up top)
    agg_tier[size_col] = agg_tier["Size (Bytes)"] * unit_factor


    st.markdown("#### 🌡️ Hot/Warm/Cold Summary")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h4 style='color:white;'>Size</h4>", unsafe_allow_html=True)
        fig_size = px.bar(
            agg_tier,
            x="Key",
            y=size_col,            # now picks up Size (GB), Size (TB), or Size (PB)
            color="Field",
            barmode="group",
            category_orders={
                "Key": ["Hot", "Warm", "Cold"],
                "Field": ["MTIME", "ATIME"]
            },
            text=agg_tier[size_col].map("{:,.2f}".format),
            labels={size_col: f"Size ({unit})"},
            template="plotly_dark",
            title=""
        )

        fig_size.update_layout(
            xaxis_title="Tier",
            yaxis_title=f"Size ({unit})",
            font=dict(color="white", size=14),
            legend=dict(title="Time Field", font=dict(color="white")),
            plot_bgcolor="#2b2d31",
            paper_bgcolor="#2b2d31"
        )
        st.plotly_chart(fig_size, use_container_width=True)



    with col2:
        st.markdown("<h4 style='color:white;'>Count</h4>", unsafe_allow_html=True)
                # Hot/Warm/Cold by Count – show MTIME vs ATIME
        fig_count = px.bar(
            agg_tier,
            x="Key",
            y="Count",
            color="Field",            # MTIME vs ATIME
            barmode="group",
            category_orders={
                "Key": ["Hot", "Warm", "Cold"],
                "Field": ["MTIME", "ATIME"]
            },
            text=agg_tier["Count"].map("{:,.0f}".format),
            template="plotly_dark",
            title=""
        )
        fig_count.update_layout(
            xaxis_title="Tier",
            yaxis_title="Count",
            font=dict(color="white"),
            plot_bgcolor="#2b2d31",
            paper_bgcolor="#2b2d31",
            legend=dict(title="Time Field", font=dict(color="white"))
        )
        st.plotly_chart(fig_count, use_container_width=True)

        # 📁 Largest Files (Top 50 by Size in selected unit)
    lf_df = view_df[view_df["Type"] == "Largest File"].copy()
    lf_df = lf_df.sort_values("Size (Bytes)", ascending=False).head(50)
    lf_df["File Name"] = lf_df["Key"]
    lf_df["Extension"] = lf_df["Key"].apply(lambda x: x.rsplit(".", 1)[-1] if "." in x else "")
    lf_df[size_col] = lf_df["Size (Bytes)"] * unit_factor
    lf_df["Last Modified"] = (
        pd.to_datetime(lf_df["MTime"], utc=True)
          .dt.tz_convert("America/New_York")
          .dt.strftime("%Y-%m-%d %H:%M:%S")
    )

    st.markdown(f"#### 📁 Largest Files (Top 50 by Size in {unit})")

    import plotly.graph_objects as go
    # Build the table
    fig_table = go.Figure(data=[go.Table(
        header=dict(
            values=["File Name", "Extension", f"Size ({unit})", "Last Modified"],
            fill_color="#2b2d31",
            font=dict(color="white", size=14),
            align="left"
        ),
        cells=dict(
            values=[
                lf_df["File Name"],
                lf_df["Extension"],
                lf_df[size_col].map("{:,.2f}".format),
                lf_df["Last Modified"]
            ],
            fill_color="#2b2d31",
            font=dict(color="white", size=12),
            align="left"
        )
    )])

    # Dynamically size the chart height so all rows are visible
    table_height = len(lf_df) * 25 + 50  # ~25px per row + header padding
    fig_table.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#2b2d31",
        plot_bgcolor="#2b2d31",
        height=table_height
    )

    st.plotly_chart(fig_table, use_container_width=True)


    # 📄 Generate PDF Report
    if st.button("📄 Generate PDF Report"):
        pdf = FPDF()

        # — Cover page with ToC —
        pdf.add_page()
        pdf.set_fill_color(43, 45, 49)           # dark background
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Diskover Dashboard Report", ln=True, align="C")
        pdf.ln(10)
        toc = [
            ("Top 20 Extensions by Size",     2),
            ("Extensions by Count",           3),
            ("Hot/Warm/Cold Size",            4),
            ("Hot/Warm/Cold Count",           5),
            ("Largest Files",                 6),
        ]
        pdf.set_font("Arial", "B", 12)
        for title, pg in toc:
            pdf.cell(0, 8, f"{title} ...... {pg}", ln=True)

        # — Charts (pages 2–5) —
        charts = [
            ("Top 20 Extensions by Size",   fig_ext),
            ("Extensions by Count",         fig_pie),
            ("Hot/Warm/Cold Size",          fig_size),
            ("Hot/Warm/Cold Count",         fig_count),
        ]
        for title, fig in charts:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            pio.write_image(fig, tmp.name, format="png")
            pdf.add_page()
            pdf.set_fill_color(43, 45, 49)
            pdf.rect(0, 0, pdf.w, pdf.h, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, title, ln=True, align="C")
            pdf.image(tmp.name, x=10, y=20, w=190)

        # — Largest Files table (page 6) —
        pdf.add_page()
        pdf.set_fill_color(43, 45, 49)
        pdf.rect(0, 0, pdf.w, pdf.h, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Largest Files", ln=True, align="C")
        pdf.ln(5)

        # column widths
        avail = pdf.w - pdf.l_margin - pdf.r_margin
        w_file = avail * 0.45
        w_ext  = avail * 0.10
        w_size = avail * 0.15
        w_date = avail * 0.30

        # header row
        pdf.set_font("Arial", "B", 12)
        pdf.cell(w_file, 8, "File Name",     border=1)
        pdf.cell(w_ext,  8, "Ext",           border=1)
        pdf.cell(w_size, 8, f"Size ({unit})",border=1)
        pdf.cell(w_date, 8, "Last Modified", border=1)
        pdf.ln()

        # data rows
        pdf.set_font("Arial", "", 12)
        for _, row in lf_df.iterrows():
            x0, y0 = pdf.get_x(), pdf.get_y()
            # File Name (wrap)
            pdf.multi_cell(w_file, 6, row["File Name"], border=1)
            row_h = pdf.get_y() - y0
            # Extension
            pdf.set_xy(x0 + w_file, y0)
            pdf.multi_cell(w_ext, row_h, row["Extension"], border=1)
            # Size
            pdf.set_xy(x0 + w_file + w_ext, y0)
            size_val = f"{row[size_col]:,.2f}"
            pdf.multi_cell(w_size, row_h, size_val, border=1)
            # Last Modified
            pdf.set_xy(x0 + w_file + w_ext + w_size, y0)
            pdf.multi_cell(w_date, row_h, row["Last Modified"], border=1)
            # next line
            pdf.set_xy(pdf.l_margin, y0 + row_h)

        # — Output PDF —
        out_file = f"diskover_report_{uuid.uuid4().hex}.pdf"
        pdf.output(out_file)
        with open(out_file, "rb") as f:
            st.download_button(
                "⬇️ Download PDF Report",
                f.read(),
                file_name="Diskover_Report.pdf",
                mime="application/pdf"
            )

# Close app
if st.button("❌ Close App"):
    sys.exit()
