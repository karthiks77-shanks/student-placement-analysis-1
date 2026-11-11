import io
import base64
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from database import get_db

def load_dataframes():
    with get_db() as (conn, engine):
        df_students = pd.read_sql_query("SELECT * FROM students", conn)
        df_placements = pd.read_sql_query("SELECT * FROM placements", conn)
        df_skills = pd.read_sql_query("""
            SELECT s.student_id, sk.skill_name 
            FROM student_skills ss
            JOIN students s ON ss.student_id = s.student_id
            JOIN skills sk ON ss.skill_id = sk.skill_id
        """, conn)
    return df_students, df_placements, df_skills

def calculate_kpis():
    df_students, df_placements, _ = load_dataframes()
    if df_students.empty:
        return {
            "total_students": 0, "eligible_students": 0, "placed_students": 0, 
            "placement_rate": 0.0, "avg_package": 0.0, "median_package": 0.0, 
            "max_package": 0.0, "total_offers": 0
        }

    # Offers with accepted / placed status
    accepted_offers = df_placements[df_placements['status'].isin(['Placed', 'Offer Accepted'])]
    placed_student_ids = set(accepted_offers['student_id'].unique())

    # Eligibility rules
    eligible_students = df_students[df_students['is_eligible'] == 1]
    placed_eligible_count = eligible_students['student_id'].isin(placed_student_ids).sum()
    
    total_eligible = len(eligible_students)
    rate = (placed_eligible_count / total_eligible * 100) if total_eligible > 0 else 0.0
    packages = accepted_offers['package_lpa']

    return {
        "total_students": int(len(df_students)),
        "eligible_students": int(total_eligible),
        "placed_students": int(placed_eligible_count),
        "placement_rate": round(float(rate), 2),
        "avg_package": round(float(packages.mean()), 2) if not packages.empty else 0.0,
        "median_package": round(float(packages.median()), 2) if not packages.empty else 0.0,
        "max_package": round(float(packages.max()), 2) if not packages.empty else 0.0,
        "total_offers": int(len(accepted_offers))
    }

def get_department_analysis():
    df_students, df_placements, _ = load_dataframes()
    if df_students.empty:
        return []

    accepted_offers = df_placements[df_placements['status'].isin(['Placed', 'Offer Accepted'])]
    placed_ids = set(accepted_offers['student_id'].unique())
    df_students['is_placed'] = df_students['student_id'].isin(placed_ids).astype(int)

    # Department & Year summary
    eligible = df_students[df_students['is_eligible'] == 1]
    dept_summary = eligible.groupby(['department', 'graduation_year']).agg(
        eligible_count=('student_id', 'count'),
        placed_count=('is_placed', 'sum')
    ).reset_index()

    dept_summary['placement_rate'] = (dept_summary['placed_count'] / dept_summary['eligible_count'] * 100).round(2)

    # Aggregate packages
    if not accepted_offers.empty:
        merged = pd.merge(accepted_offers, df_students[['student_id', 'department']], on='student_id')
        pkg_by_dept = merged.groupby('department')['package_lpa'].agg(
            avg_package='mean',
            highest_package='max'
        ).round(2).reset_index()
        final_report = pd.merge(dept_summary, pkg_by_dept, on='department', how='left').fillna(0)
    else:
        dept_summary['avg_package'] = 0.0
        dept_summary['highest_package'] = 0.0
        final_report = dept_summary

    return final_report.to_dict(orient='records')

def get_skill_demand():
    _, df_placements, df_skills = load_dataframes()
    if df_skills.empty:
        return []

    placed_ids = set(df_placements[df_placements['status'].isin(['Placed', 'Offer Accepted'])]['student_id'])
    placed_skills = df_skills[df_skills['student_id'].isin(placed_ids)]
    
    counts = placed_skills['skill_name'].value_counts().reset_index()
    counts.columns = ['skill_name', 'count']
    return counts.head(10).to_dict(orient='records')

def apply_modern_chart_style(ax, fig):
    """Applies a clean, modern, borderless SaaS dashboard style to Matplotlib figures."""
    fig.patch.set_facecolor('#ffffff')
    fig.patch.set_alpha(0.0)
    ax.set_facecolor('#ffffff')
    ax.grid(True, linestyle='--', alpha=0.35, color='#cbd5e1', zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#94a3b8')
    ax.spines['bottom'].set_color('#94a3b8')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors='#475569', labelsize=8.5)

def generate_charts():
    df_students, df_placements, df_skills = load_dataframes()
    charts = {}

    plt.rcParams['font.sans-serif'] = ['Segoe UI', 'DejaVu Sans', 'Arial']
    plt.rcParams['font.family'] = 'sans-serif'

    # Chart 1: Placement Rate by Department (Modern Gradient/Color Bar Chart)
    if not df_students.empty and not df_placements.empty:
        fig, ax = plt.subplots(figsize=(6.8, 3.8))
        apply_modern_chart_style(ax, fig)

        placed_ids = set(df_placements[df_placements['status'].isin(['Placed', 'Offer Accepted'])]['student_id'])
        df_students['is_placed'] = df_students['student_id'].isin(placed_ids).astype(int)
        
        rates = df_students[df_students['is_eligible'] == 1].groupby('department').apply(
            lambda x: (x['is_placed'].sum() / len(x) * 100) if len(x) > 0 else 0
        )
        
        # Color gradient palette across departments
        palette = ['#2563eb', '#3b82f6', '#0ea5e9', '#06b6d4', '#10b981', '#f59e0b']
        colors = [palette[i % len(palette)] for i in range(len(rates))]
        
        bars = ax.bar(rates.index, rates.values, color=colors, edgecolor='none', width=0.52, zorder=3, alpha=0.92)
        ax.set_title('Placement Rate (%) by Department', fontsize=11, fontweight='bold', pad=12, color='#0f172a')
        ax.set_ylabel('Placement Rate (%)', fontsize=9, color='#475569', labelpad=8)
        ax.set_ylim(0, 105)
        plt.xticks(rotation=18, ha='right', fontsize=8.5)

        for b in bars:
            h = b.get_height()
            ax.annotate(f'{h:.1f}%', xy=(b.get_x() + b.get_width() / 2, h),
                        xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', 
                        fontsize=8.5, fontweight='bold', color='#1e293b')
        plt.tight_layout()
        charts['dept_chart'] = fig_to_base64(fig)
        plt.close(fig)

    # Chart 2: Package Distribution (Modern Smooth Distribution)
    if not df_placements.empty:
        fig, ax = plt.subplots(figsize=(6.8, 3.8))
        apply_modern_chart_style(ax, fig)

        pkgs = df_placements[df_placements['status'].isin(['Placed', 'Offer Accepted'])]['package_lpa']
        if not pkgs.empty:
            n, bins, patches = ax.hist(pkgs, bins=8, color='#10b981', edgecolor='#ffffff', linewidth=1.5, alpha=0.88, zorder=3)
            # Apply golden highlight to highest package bin
            if len(patches) > 0:
                patches[-1].set_facecolor('#f59e0b')

            ax.axvline(pkgs.median(), color='#ef4444', linestyle='--', linewidth=2, label=f'Median: {pkgs.median():.2f} LPA', zorder=4)
            ax.axvline(pkgs.mean(), color='#6366f1', linestyle=':', linewidth=2, label=f'Mean: {pkgs.mean():.2f} LPA', zorder=4)
            ax.set_title('Salary Package Distribution (LPA)', fontsize=11, fontweight='bold', pad=12, color='#0f172a')
            ax.set_xlabel('Package (LPA)', fontsize=9, color='#475569', labelpad=8)
            ax.set_ylabel('Number of Offers', fontsize=9, color='#475569', labelpad=8)
            ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=8.5, loc='upper right')
            plt.tight_layout()
            charts['pkg_chart'] = fig_to_base64(fig)
        plt.close(fig)

    # Chart 3: Skill Demand (Sleek Horizontal Bar Chart with Golden Gradient Feel)
    if not df_skills.empty:
        fig, ax = plt.subplots(figsize=(6.8, 3.8))
        apply_modern_chart_style(ax, fig)

        top_s = df_skills['skill_name'].value_counts().head(8)
        if not top_s.empty:
            # Color gradient from violet to golden amber
            skill_colors = ['#8b5cf6', '#7c3aed', '#6366f1', '#4f46e5', '#3b82f6', '#0284c7', '#0d9488', '#f59e0b']
            bars = ax.barh(top_s.index[::-1], top_s.values[::-1], color=skill_colors[:len(top_s)][::-1], 
                          height=0.55, edgecolor='none', zorder=3, alpha=0.9)
            ax.set_title('Top In-Demand Skills in Placements', fontsize=11, fontweight='bold', pad=12, color='#0f172a')
            ax.set_xlabel('Student Profiles Placed with Skill', fontsize=9, color='#475569', labelpad=8)
            
            for b in bars:
                w = b.get_width()
                ax.annotate(f' {int(w)}', xy=(w, b.get_y() + b.get_height() / 2),
                            xytext=(2, 0), textcoords="offset points", ha='left', va='center',
                            fontsize=8.5, fontweight='bold', color='#334155')
            plt.tight_layout()
            charts['skill_chart'] = fig_to_base64(fig)
        plt.close(fig)

    return charts

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=140, bbox_inches='tight', transparent=True)
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
