def asx_brokerage(amount_aud: float, qualifying_buy: bool = False, minimum: float = 11.0, rate_pct: float = 0.10) -> float:
    if qualifying_buy and amount_aud <= 999:
        return 0.0
    return max(minimum, amount_aud * rate_pct / 100)


def brokerage_drag(amount_aud: float, **kwargs: object) -> float:
    return asx_brokerage(amount_aud, **kwargs) / amount_aud * 100
