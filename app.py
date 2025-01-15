import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# 1) Mortgage & Cash Flow Helpers
# ----------------------------

def monthly_mortgage_payment(property_value, down_payment_pct, annual_interest_rate, years):
    """
    Compute the monthly mortgage payment given:
      - property_value
      - down_payment_pct (e.g., 0.20 for 20%)
      - annual_interest_rate (decimal, e.g., 0.0717 for 7.17%)
      - term in years (e.g., 30)
    """
    loan_amount = (1 - down_payment_pct) * property_value
    monthly_interest_rate = annual_interest_rate / 12
    n = years * 12
    # Standard mortgage formula
    m = loan_amount * monthly_interest_rate * (1 + monthly_interest_rate)**n / ((1 + monthly_interest_rate)**n - 1)
    return m

def required_rent(property_value, down_payment_pct, annual_interest_rate, years,
                  tax_rate_pct, annual_insurance, vacancy_capex_rate, monthly_hoa):
    """
    Calculate the monthly rent required to be cash-flow positive (break-even) in Year 1.
      - Property Tax = tax_rate_pct * property_value
      - Insurance = annual_insurance
      - Mortgage = 12 * monthly_mortgage_payment()
      - HOA = 12 * monthly_hoa
      - Vacancy+CapEx = vacancy_capex_rate * (12 * rent)
    => Net Income = 12 * Rent - (all expenses) >= 0
    """
    annual_tax = tax_rate_pct * property_value
    annual_mortgage = 12 * monthly_mortgage_payment(property_value, down_payment_pct, annual_interest_rate, years)
    annual_hoa = 12 * monthly_hoa

    fixed_annual_expenses = annual_tax + annual_insurance + annual_mortgage + annual_hoa
    denom = 12 * (1 - vacancy_capex_rate)

    # Rent needed so that (12*Rent - variable costs) >= fixed_annual_expenses
    rent = fixed_annual_expenses / denom
    return rent

# ----------------------------
# 2) Year-by-Year Cash Flow & ROI
# ----------------------------

def net_annual_cash_flow_year(
    year_index,
    base_property_value,
    base_rent,
    tax_rate_pct,
    annual_insurance,
    monthly_mortgage,
    monthly_hoa,
    vacancy_capex_rate,
    rent_growth,
    appreciation,
    other_costs_growth
):
    """
    Calculate the net annual cash flow for a given year_index (1-based), assuming:
      - property_value grows by 'appreciation' each year
      - rent grows by 'rent_growth' each year
      - insurance, HOA, etc. grow by 'other_costs_growth' each year
      - mortgage payment is fixed (assuming a fixed-rate loan)
    """
    # Growth factors
    rent_factor = (1 + rent_growth)**(year_index - 1)
    prop_factor = (1 + appreciation)**(year_index - 1)
    cost_factor = (1 + other_costs_growth)**(year_index - 1)

    # Current year property value
    property_value_yr = base_property_value * prop_factor

    # Current year annual rent
    annual_rent_yr = 12 * base_rent * rent_factor

    # Current year property tax
    annual_tax_yr = tax_rate_pct * property_value_yr

    # Current year insurance (assume it grows by other_costs_growth)
    annual_insurance_yr = annual_insurance * cost_factor

    # Current year HOA (assume monthly HOA also grows by other_costs_growth)
    annual_hoa_yr = monthly_hoa * 12 * cost_factor

    # Mortgage (fixed) = monthly_mortgage * 12, ignoring small changes in real amortization
    annual_mortgage_yr = monthly_mortgage * 12

    # Vacancy + CapEx (same total % of that year's rent)
    vacancy_capex_yr = vacancy_capex_rate * annual_rent_yr

    total_annual_expenses = (annual_tax_yr
                             + annual_insurance_yr
                             + annual_mortgage_yr
                             + annual_hoa_yr
                             + vacancy_capex_yr)

    net_cf_yr = annual_rent_yr - total_annual_expenses
    return net_cf_yr

def compute_annual_roi_list(
    num_years,
    base_property_value,
    base_rent,
    down_payment_pct,
    annual_interest_rate,
    years,  # loan term
    tax_rate_pct,
    annual_insurance,
    monthly_hoa,
    vacancy_capex_rate,
    rent_growth,
    appreciation,
    other_costs_growth,
    closing_costs
):
    """
    Return a list of (year_index, net_annual_cash_flow, ROI%) from 1..num_years
      ROI% = Net CF / Initial Investment * 100
    """
    # 1) Mortgage payment (fixed)
    monthly_mort = monthly_mortgage_payment(
        base_property_value, down_payment_pct, annual_interest_rate, years
    )

    # 2) Initial Investment
    down_payment = down_payment_pct * base_property_value
    initial_investment = down_payment + closing_costs

    # 3) Build results
    results = []
    for i in range(1, num_years + 1):
        net_cf_yr_i = net_annual_cash_flow_year(
            year_index = i,
            base_property_value = base_property_value,
            base_rent = base_rent,
            tax_rate_pct = tax_rate_pct,
            annual_insurance = annual_insurance,
            monthly_mortgage = monthly_mort,
            monthly_hoa = monthly_hoa,
            vacancy_capex_rate = vacancy_capex_rate,
            rent_growth = rent_growth,
            appreciation = appreciation,
            other_costs_growth = other_costs_growth
        )
        roi_i = (net_cf_yr_i / initial_investment) * 100 if initial_investment != 0 else 0
        results.append((i, net_cf_yr_i, roi_i))
    return results

# ----------------------------
# 3) Main Streamlit App
# ----------------------------
def main():
    st.title("Real Estate Calculator with HOA & Year-on-Year ROI")

    st.sidebar.header("Inputs & Assumptions")

    # --- Common Inputs ---
    purchase_price = st.sidebar.number_input("Purchase Price ($)", 
                                             min_value=50_000, 
                                             max_value=5_000_000, 
                                             value=480_000, 
                                             step=10_000)

    down_payment_pct = st.sidebar.slider("Down Payment (%)", 
                                         min_value=0.0, 
                                         max_value=1.0, 
                                         value=0.20, 
                                         step=0.01)
    
    closing_costs = st.sidebar.number_input("Closing Costs ($)",
                                            min_value=0.0, 
                                            max_value=50_000.0,
                                            value=14_400.0,
                                            step=1_000.0)

    annual_interest_rate = st.sidebar.slider("Annual Interest Rate (%)", 
                                             min_value=0.0, 
                                             max_value=0.20, 
                                             value=0.0717, 
                                             step=0.0001)
    
    years = st.sidebar.slider("Loan Term (Years)", 
                              min_value=1, 
                              max_value=40, 
                              value=30, 
                              step=1)

    tax_rate_pct = st.sidebar.slider("Tax Rate (% of Value)", 
                                     min_value=0.0, 
                                     max_value=0.05, 
                                     value=0.015, 
                                     step=0.001)

    annual_insurance = st.sidebar.number_input("Annual Insurance ($)", 
                                               min_value=0.0, 
                                               max_value=10_000.0, 
                                               value=1_000.0, 
                                               step=100.0)
    
    vacancy_capex_rate = st.sidebar.slider("Vacancy + CapEx (% of Rent)", 
                                           min_value=0.0, 
                                           max_value=0.30, 
                                           value=0.10, 
                                           step=0.01)
    
    monthly_hoa = st.sidebar.number_input("Monthly HOA ($)", 
                                          min_value=0.0, 
                                          max_value=2_000.0, 
                                          value=0.0, 
                                          step=50.0)

    # --- Growth Assumptions ---
    st.sidebar.header("Growth Assumptions")
    rent_growth = st.sidebar.slider("Annual Rent Growth (%)", 0.0, 0.10, 0.02, 0.005)
    appreciation = st.sidebar.slider("Annual Appreciation (%)", 0.0, 0.10, 0.02, 0.005)
    other_costs_growth = st.sidebar.slider("Other Costs Growth (%)", 0.0, 0.10, 0.02, 0.005)

    # -- Using tabs to separate functionalities --
    tab1, tab2 = st.tabs(["Required Rent", "ROI Calculation"])

    # --------------------------------------------------
    # Tab 1: Required Rent (Year 1)
    # --------------------------------------------------
    with tab1:
        st.subheader("1. Required Monthly Rent to Break Even (Year 1)")

        monthly_mortgage = monthly_mortgage_payment(
            purchase_price,
            down_payment_pct,
            annual_interest_rate,
            years
        )
        needed_rent_year1 = required_rent(
            purchase_price,
            down_payment_pct,
            annual_interest_rate,
            years,
            tax_rate_pct,
            annual_insurance,
            vacancy_capex_rate,
            monthly_hoa
        )

        st.write(f"**Monthly Mortgage Payment (Fixed):** ${monthly_mortgage:,.2f}")
        st.write(f"**Required Monthly Rent (Year 1 Break Even):** ${needed_rent_year1:,.2f}")

        st.markdown("---")
        st.subheader("Plot: Required Rent vs. Property Value (Year 1 Only)")
        st.write("See how the Year 1 break-even rent changes with property value.")
        
        min_val = st.number_input("Min Property Value", value=400_000, step=10_000)
        max_val = st.number_input("Max Property Value", value=2_000_000, step=10_000)
        num_points = st.slider("Number of Points in Range", min_value=10, max_value=200, value=50)

        values = np.linspace(min_val, max_val, num_points)
        rents = []
        for v in values:
            r = required_rent(
                v,
                down_payment_pct,
                annual_interest_rate,
                years,
                tax_rate_pct,
                annual_insurance,
                vacancy_capex_rate,
                monthly_hoa
            )
            rents.append(r)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(values, rents, color='blue', label='Required Rent (Year 1)')
        ax.set_title("Required Monthly Rent vs. Property Value (Year 1)")
        ax.set_xlabel("Property Value ($)")
        ax.set_ylabel("Required Monthly Rent ($)")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

        st.write("""
        **Interpretation**:
        - Higher property value -> bigger mortgage + higher taxes -> higher required rent.
        - HOA adds a fixed monthly cost, increasing needed rent.
        """)

    # --------------------------------------------------
    # Tab 2: ROI Calculation (Year-by-Year)
    # --------------------------------------------------
    with tab2:
        st.subheader("2. Year-by-Year ROI")

        st.write("""
        Adjust your **actual rent** (starting rent in Year 1). We then grow it by the rent growth 
        rate each year. Taxes and other expenses also adjust each year based on the 
        appreciation and other cost growth rates.
        """)

        actual_rent_year1 = st.number_input(
            "Actual Monthly Rent in Year 1 ($)", 
            min_value=0.0, 
            max_value=10_000.0, 
            value=2_500.0, 
            step=100.0
        )

        # Number of years for ROI plot
        roi_horizon = st.slider("Number of Years to Project", min_value=1, max_value=30, value=10)

        # Compute year-by-year net CF & ROI
        roi_data = compute_annual_roi_list(
            num_years = roi_horizon,
            base_property_value = purchase_price,
            base_rent = actual_rent_year1,
            down_payment_pct = down_payment_pct,
            annual_interest_rate = annual_interest_rate,
            years = years,
            tax_rate_pct = tax_rate_pct,
            annual_insurance = annual_insurance,
            monthly_hoa = monthly_hoa,
            vacancy_capex_rate = vacancy_capex_rate,
            rent_growth = rent_growth,
            appreciation = appreciation,
            other_costs_growth = other_costs_growth,
            closing_costs = closing_costs
        )

        # Display results in a table
        st.write("**Year-by-Year Cash Flow & ROI**")
        st.write("| Year | Net Annual CF ($) | ROI (%) |")
        st.write("|------|--------------------|---------|")
        for (year_idx, net_cf, roi_pct) in roi_data:
            st.write(f"| {year_idx} | ${net_cf:,.2f} | {roi_pct:,.2f}% |")

        # Plot Year vs. ROI
        years_list = [d[0] for d in roi_data]
        roi_vals = [d[2] for d in roi_data]

        fig2, ax2 = plt.subplots(figsize=(8, 5))
        ax2.plot(years_list, roi_vals, marker='o', color='green', label='Annual ROI %')
        ax2.set_title("Year-by-Year ROI (%)")
        ax2.set_xlabel("Year")
        ax2.set_ylabel("ROI (%)")
        ax2.grid(True)
        ax2.legend()
        st.pyplot(fig2)

        st.write("""
        **Interpretation**:
        - **Net Annual Cash Flow** changes each year because:
          - Rent grows at your specified rate.
          - Property taxes grow with appreciation.
          - Insurance, HOA, etc. grow at 'Other Costs Growth'.
          - Mortgage is fixed (monthly payment doesn't change).
        - **ROI** = (Year N Net Cash Flow ÷ Initial Investment) × 100%.
          This is a simple measure of annual return relative to your upfront cash (down payment + closing).
        - You may also consider principal paydown or appreciation in a more advanced ROI (e.g., 
          total equity or an IRR calculation), but this example focuses on cash flow ROI.
        """)

if __name__ == "__main__":
    main()
