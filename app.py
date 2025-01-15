import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def monthly_mortgage_payment(property_value, down_payment_pct, annual_interest_rate, years):
    """
    Compute the monthly mortgage payment given:
      - property_value
      - down_payment_pct (e.g., 0.20 for 20%)
      - annual_interest_rate (e.g., 0.0717 for 7.17%)
      - term in years (e.g., 30)
    """
    loan_amount = (1 - down_payment_pct) * property_value
    monthly_interest_rate = annual_interest_rate / 12
    n = years * 12
    # Mortgage payment formula
    m = loan_amount * monthly_interest_rate * (1 + monthly_interest_rate)**n / ((1 + monthly_interest_rate)**n - 1)
    return m

def required_rent(property_value, down_payment_pct, annual_interest_rate, years,
                  tax_rate_pct, annual_insurance, vacancy_capex_rate,
                  monthly_hoa):
    """
    Compute the monthly rent required to be cash-flow positive.
    We consider:
      - Property tax:    tax_rate_pct * property_value
      - Insurance:       annual_insurance (fixed $/yr)
      - Mortgage:        12 * monthly_mortgage_payment()
      - HOA:             12 * monthly_hoa
      - Vacancy+CapEx:   vacancy_capex_rate * (12 * rent)
    => Net Income = 12*Rent - (tax + insurance + mortgage + HOA + Vacancy+CapEx) >= 0
    """
    # Annual amounts
    tax = tax_rate_pct * property_value
    annual_mortgage = 12 * monthly_mortgage_payment(
        property_value, down_payment_pct, annual_interest_rate, years
    )
    annual_hoa = 12 * monthly_hoa

    # Numerator: total fixed annual costs (tax + insurance + mortgage + HOA)
    numerator = tax + annual_insurance + annual_mortgage + annual_hoa

    # Denominator: 12*(1 - vacancy_capex_rate)
    denom = 12 * (1 - vacancy_capex_rate)

    # Required monthly rent
    rent = numerator / denom
    return rent

def main():
    st.title("Cash-Flow Positive Rent Calculator (with HOA)")

    st.write("""
    This app calculates **monthly mortgage** and the **rent required** to be 
    cash-flow positive, given real estate assumptions **including an HOA fee**.
    """)

    # --- Sidebar Inputs ---
    st.sidebar.header("Inputs & Assumptions")
    
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

    tax_rate_pct = st.sidebar.slider("Tax Rate (% of Property Value)", 
                                     min_value=0.0, 
                                     max_value=0.05, 
                                     value=0.015, 
                                     step=0.001)
    annual_insurance = st.sidebar.number_input("Annual Insurance ($)", 
                                               min_value=0.0, 
                                               max_value=10_000.0, 
                                               value=1_000.0, 
                                               step=100.0)
    vacancy_capex_rate = st.sidebar.slider("Vacancy + CapEx Rate (% of Rent)", 
                                           min_value=0.0, 
                                           max_value=0.30, 
                                           value=0.10, 
                                           step=0.01)
    monthly_hoa = st.sidebar.number_input("HOA Fee (Monthly $)", 
                                          min_value=0.0, 
                                          max_value=2_000.0, 
                                          value=0.0, 
                                          step=50.0)

    # --- Calculations for a single property price ---
    monthly_mortgage = monthly_mortgage_payment(
        purchase_price,
        down_payment_pct,
        annual_interest_rate,
        years
    )
    needed_rent = required_rent(
        purchase_price,
        down_payment_pct,
        annual_interest_rate,
        years,
        tax_rate_pct,
        annual_insurance,
        vacancy_capex_rate,
        monthly_hoa
    )

    st.subheader("1. Single-Value Calculation")
    st.write(f"**Monthly Mortgage Payment:** ${monthly_mortgage:,.2f}")
    st.write(f"**Required Monthly Rent (to Break Even):** ${needed_rent:,.2f}")

    st.markdown("---")
    st.subheader("2. Plot: Required Rent vs. Property Value")
    st.write("""
    Use the range below to see how required monthly rent changes as property value varies.
    """)

    # Range inputs
    min_value = st.number_input("Min Property Value", value=400_000, step=10_000)
    max_value = st.number_input("Max Property Value", value=2_000_000, step=10_000)
    num_points = st.slider("Number of Points in Range", min_value=10, max_value=200, value=50)

    # Generate data
    values = np.linspace(min_value, max_value, num_points)
    rents = [
        required_rent(
            v,
            down_payment_pct,
            annual_interest_rate,
            years,
            tax_rate_pct,
            annual_insurance,
            vacancy_capex_rate,
            monthly_hoa
        )
        for v in values
    ]

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(values, rents, label='Required Monthly Rent', color='blue')
    ax.set_title("Required Monthly Rent vs. Property Value (HOA included)")
    ax.set_xlabel("Property Value ($)")
    ax.set_ylabel("Required Monthly Rent ($)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    st.write("""
    **Interpretation**:
    - As the property value goes up, loan amount and property tax go up.
    - With HOA added, monthly expenses are higher, so the required rent will increase.
    """)

if __name__ == "__main__":
    main()
