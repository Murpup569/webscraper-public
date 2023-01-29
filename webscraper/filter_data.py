"""Filter data from website"""
from decimal import Decimal


def format_data_to_list(df_venue):
    """Filter and format data"""
    venue_data = list(
        map(
            list,
            zip(
                df_venue.SpotName.to_numpy(),
                df_venue.License_Number.to_numpy(),
                df_venue.FundsIn.to_numpy(),
                df_venue.FundsOut.to_numpy(),
                df_venue.NetTerminalIncome.to_numpy(),
                df_venue.Location_Share.to_numpy(),
            ),
        )
    )
    return venue_data


def clean_cash_string(input_value):
    """If the value is a string, then remove currency symbol and delimiters
    otherwise, the value is numeric and can be converted
    """
    if isinstance(input_value, str):
        if "(" in input_value:
            output_value = (
                input_value.replace("$", "")
                .replace(",", "")
                .replace("(", "-")
                .replace(")", "")
            )
        else:
            output_value = input_value.replace("$", "").replace(",", "")
    return output_value


def add_cash_string(input_value):
    """If the value is a string, then remove currency symbol and delimiters
    otherwise, the value is numeric and can be converted
    """
    if isinstance(input_value, str):
        if "-" in input_value:
            output_value = f'({input_value.replace("-", "-$")})'
        else:
            output_value = f"${input_value}"
    return output_value


def get_location_share(input_value):
    """Calculate location share"""
    return str(round(Decimal(input_value) * Decimal("0.335"), 2))


def clean_currency(df_venue):
    """Remove any dollar signs and parentheses"""
    df_venue_clean = df_venue.copy()
    df_venue_clean["FundsIn"] = df_venue["FundsIn"].apply(clean_cash_string)
    df_venue_clean["FundsOut"] = df_venue["FundsOut"].apply(clean_cash_string)
    df_venue_clean["NetTerminalIncome"] = df_venue["NetTerminalIncome"].apply(
        clean_cash_string
    )
    return df_venue_clean


def add_decimal(data_frame, column):
    """Convert to decimal and add and return with dollar sign."""
    count = Decimal("0")
    for item in data_frame[column]:
        count = count + Decimal(item)
    return count


def create_sum_table(df_venue_clean, yesterday):
    """Add up rows in data frame and add dollar signs"""
    funds_in = add_decimal(df_venue_clean, "FundsIn")
    funds_out = add_decimal(df_venue_clean, "FundsOut")
    net_terminal_income = add_decimal(df_venue_clean, "NetTerminalIncome")
    location_share = add_decimal(df_venue_clean, "Location_Share")
    return [
        f"Totals for {yesterday}:",
        "",
        add_cash_string(str(funds_in)),
        add_cash_string(str(funds_out)),
        add_cash_string(str(net_terminal_income)),
        add_cash_string(str(location_share)),
    ]


def add_dollar_sign_and_format_negative(df_venue_clean):
    """Add dollar signs, negative, and parentheses"""
    df_venue_with_dollar = df_venue_clean.copy()
    df_venue_with_dollar["FundsIn"] = df_venue_clean["FundsIn"].apply(add_cash_string)
    df_venue_with_dollar["FundsOut"] = df_venue_clean["FundsOut"].apply(add_cash_string)
    df_venue_with_dollar["NetTerminalIncome"] = df_venue_clean[
        "NetTerminalIncome"
    ].apply(add_cash_string)
    df_venue_with_dollar["Location_Share"] = df_venue_clean["Location_Share"].apply(
        add_cash_string
    )
    return df_venue_with_dollar
