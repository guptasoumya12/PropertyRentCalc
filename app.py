import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# Helper Functions
# ----------------------------

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
                  tax_rate_pct, annual_insurance, vacancy_capex_rate, monthly_hoa):
    """
    Calculate the monthly rent required to be cash-flow positive (break-even).
    We consider:
      - Property Tax = tax_rate_pct * property_value
      - Insurance = annual_insurance (fixed $)
      - Mortgage = 12 * monthly_mortgage_payment
      - HOA = 12 * monthly_hoa
      - Vacancy+CapEx = vacancy_capex_rate * (12 * rent)
    => Net Income = 12*Rent - [tax + insurance + mortgage + HOA + (Vacancy+CapEx)] >= 0
    """
    # Annual amounts
    annual_tax = tax_rate_pct * property_value
    annual_mortgage = 12 * monthly_mortgage_payment(property_value, down_payment_pct, annual_interest_rate, years)
    annual_hoa = 12 * monthly_hoa

    # Combine fixed expenses
    fixed_annual_expenses = annual_tax + annual_insurance + annual_mortgage + annual_hoa

    # Required rent formula:
    # 12*Rent - (fixed_annual_expenses + vacancy_capex_rate*(12*Rent)) >= 0
    # 12*Rent*(1 - vacancy_capex_rate) >= fixed_annual_expenses
    # Rent >= fixed_annual_expenses / [12*(1 - vacancy_capex_rate)]
    denom = 12 * (1 - vacancy_capex_rate)
    rent = fixed_annual_expenses / denom
    return rent

def net_annual_cash_flow(
    property_value,
    down_payment_pct,
    annual_interest_rate,
    years,
    tax_rate_pct,
    annual_insurance,
    vacancy_capex_rate,
    monthly_hoa,
    monthly_rent
):
    """
    Calculate the net annual cash flow given an actual monthly_rent.
    """
    annual_gross_rent = monthly_rent * 12
    
    # Annual Expenses
    annual_tax = tax_rate_pct * property_value
    annual_mortgage = 12 * monthly_mortgage_payment(property_value, down_payment_pct, annual_interest_rate, years)
    annual_hoa = 12 * monthly_hoa
    vacancy_capex = vacancy_capex_rate * (annual_gross_rent)  # total for vacancy + capex

    total_annual_expenses = annual_tax + annual_insurance + annual_mortgage + annual_hoa + vacancy_capex
    
    return annual_gross_rent - total_annual_expenses

def compute_roi(net_annual_cf, down_payment, closing_costs):
    """
    Simple ROI = (Net Annual Cash Flow / Initial Investment) * 100%
    """
    initial_investment = down_payment + closing_costs
    if initial_investment == 0:
        return 0.0
    return (net_annual_cf / initial_investment) * 100


# ----------------------------
# Main Streamlit App
# ----------------------------
def main():
    st.title("Real Estate Calculator with HOA & ROI")

    st.sidebar.header("Inputs & Assumptions")

    # Common Inputs
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
                                            step=1_000.0,
                                            help="Enter your total closing costs in USD.")

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

    # -- Using tabs to separate functionalities --
    tab1, tab2 = st.tabs(["Required Rent", "ROI Calculation"])

    # -------------------------------------------
    # Tab 1: Required Rent (Cash Flow Positive)
    # -------------------------------------------
    with tab1:
        st.subheader("1. Required Rent to Break Even")
        
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

        st.write(f"**Monthly Mortgage Payment:** ${monthly_mortgage:,.2f}")
        st.write(f"**Required Monthly Rent (to Break Even):** ${needed_rent:,.2f}")

        # Plot: property values vs. required rent
        st.markdown("---")
        st.subheader("Plot: Required Rent vs. Property Value")
        st.write("Use the range below to see how the required rent changes as property value varies.")
        
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
        ax.plot(values, rents, color='blue', label='Required Monthly Rent')
        ax.set_title("Required Monthly Rent vs. Property Value (HOA included)")
        ax.set_xlabel("Property Value ($)")
        ax.set_ylabel("Required Monthly Rent ($)")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

        st.write("""
        **Interpretation**:
        - Higher property value -> larger mortgage + higher taxes -> higher required rent.
        - HOA also adds a fixed monthly cost, increasing needed rent.
        """)

    # -------------------------------------------
    # Tab 2: ROI Calculation
    # -------------------------------------------
    with tab2:
        st.subheader("2. Return on Investment (ROI)")

        st.write("""
        This tab calculates your net annual cash flow and ROI based on an **actual** monthly rent. 
        Adjust the rent below to see how it affects your annual return.
        """)

        actual_rent = st.number_input(
            "Actual Monthly Rent ($)", 
            min_value=0.0, 
            max_value=10_000.0, 
            value=2_500.0, 
            step=100.0
        )

        # Calculate net annual cash flow
        nacf = net_annual_cash_flow(
            property_value = purchase_price,
            down_payment_pct = down_payment_pct,
            annual_interest_rate = annual_interest_rate,
            years = years,
            tax_rate_pct = tax_rate_pct,
            annual_insurance = annual_insurance,
            vacancy_capex_rate = vacancy_capex_rate,
            monthly_hoa = monthly_hoa,
            monthly_rent = actual_rent
        )

        # Calculate initial investment
        down_payment = down_payment_pct * purchase_price
        # We treat 'closing_costs' as a separate input (sidebar).
        initial_investment = down_payment + closing_costs

        # ROI
        roi_percent = compute_roi(nacf, down_payment, closing_costs)

        st.write(f"**Net Annual Cash Flow:** ${nacf:,.2f}")
        st.write(f"**Initial Investment:** ${initial_investment:,.2f}")
        st.write(f"**ROI:** {roi_percent:,.2f}%")

        st.markdown("""
        ---
        **Notes**:
        - **Net Annual Cash Flow** = (12 × Actual Rent) - (Mortgage, Taxes, Insurance, HOA, Vacancy/CapEx).
        - **Initial Investment** = (Down Payment + Closing Costs).
        - **ROI** = (Net Annual Cash Flow / Initial Investment) × 100
        """)

if __name__ == "__main__":
    main()
