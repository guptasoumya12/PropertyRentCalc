import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Streamlit requires "magic" to ensure inline plotting
st.set_option('deprecation.showPyplotGlobalUse', False)

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
                  tax_rate_pct, annual_insurance, vacancy_capex_rate):
    """
    Compute the monthly rent required to be cash-flow positive:
      Annual Cash Flow = (12 * Rent) - Expenses >= 0
    Where:
      Expenses = 
          1) Property Tax (tax_rate_pct * value) 
          2) Insurance (annual_insurance)
          3) Mortgage (12 * monthly_mortgage_payment)
          4) Vacancy (5% of rent)
          5) CapEx (5% of rent)
    Combined, Vacancy + CapEx = vacancy_capex_rate of gross rent (10% by default).
    """
    # 1) Annual property tax
    tax = tax_rate_pct * property_value
    
    # 2) Annual mortgage payment
    annual_mortgage = 12 * monthly_mortgage_payment(
        property_value, 
        down_payment_pct, 
        annual_interest_rate, 
        years
    )
    
    # Numerator of the formula: taxes + insurance + mortgage
    numerator = tax + annual_insurance + annual_mortgage
    
    # Denominator = 12 * (1 - vacancy_capex_rate)
    denom = 12 * (1 - vacancy_capex_rate)
    
    # Required monthly rent
    rent = numerator / denom
    return rent

def main():
    st.title("Cash-Flow Positive Rent Calculator")

    st.write("""
    This simple app calculates the **monthly mortgage** and the **rent required** to be 
    cash-flow positive (breakeven or better), given some real estate assumptions.
    """)

    # --- Sidebar Inputs ---
    st.sidebar.header("Inputs & Assumptions")
    
    purchase_price = st.sidebar.number_input("Purchase Price ($)", min_value=50000, max_value=5000000, value=480000, step=10000)
    down_payment_pct = st.sidebar.slider("Down Payment (%)", min_value=0.0, max_value=1.0, value=0.20, step=0.01)
    annual_interest_rate = st.sidebar.slider("Annual Interest Rate (%)", min_value=0.0, max_value=0.20, value=0.0717, step=0.0001)
    years = st.sidebar.slider("Loan Term (Years)", min_value=1, max_value=40, value=30, step=1)

    tax_rate_pct = st.sidebar.slider("Tax Rate (% of Property Value)", min_value=0.0, max_value=0.05, value=0.015, step=0.001)
    annual_insurance = st.sidebar.number_input("Annual Insurance ($)", min_value=0.0, max_value=10000.0, value=1000.0, step=100.0)
    vacancy_capex_rate = st.sidebar.slider("Vacancy + CapEx Rate (% of Rent)", min_value=0.0, max_value=0.30, value=0.10, step=0.01)
    
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
        vacancy_capex_rate
    )

    st.subheader("1. Single-Value Calculation")
    st.write(f"**Monthly Mortgage Payment:** ${monthly_mortgage:,.2f}")
    st.write(f"**Required Monthly Rent to Break Even:** ${needed_rent:,.2f}")

    st.markdown("---")
    st.subheader("2. Plot: Required Rent vs. Property Value")
    st.write("""
    You can specify a range of property values below (e.g., \$400k to \$2M). 
    The chart will show the required monthly rent for each property value to be at least break-even.
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
            vacancy_capex_rate
        )
        for v in values
    ]

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(values, rents, label='Required Monthly Rent', color='blue')
    ax.set_title("Required Monthly Rent vs. Property Value")
    ax.set_xlabel("Property Value ($)")
    ax.set_ylabel("Required Monthly Rent ($)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    st.write("""
    **Interpretation**:
    - As the property value goes up, the loan amount typically increases (assuming the same down payment %),
      so your mortgage payment and property taxes will be higher.
    - Consequently, the rent required to break even also rises.
    """)

if __name__ == "__main__":
    main()
