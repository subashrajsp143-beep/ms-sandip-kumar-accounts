"""
Indian Currency to Words Converter for M/S Sandip Kumar Vouchers
Formats numbers into Indian numbering system: Crores, Lakhs, Thousands, Hundreds
"""

def number_to_indian_words(num):
    try:
        num = float(num)
    except (ValueError, TypeError):
        return "Zero Rupees Only"
    
    if num == 0:
        return "Zero Rupees Only"
    
    if num < 0:
        return "Minus " + number_to_indian_words(abs(num))
    
    integer_part = int(num)
    paisa_part = int(round((num - integer_part) * 100))
    
    ones = [
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"
    ]
    tens = [
        "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
    ]

    def two_digits(n):
        if n == 0:
            return ""
        elif n < 20:
            return ones[n]
        else:
            t = tens[n // 10]
            o = ones[n % 10]
            return (t + " " + o).strip()

    def three_digits(n):
        h = n // 100
        rem = n % 100
        res = ""
        if h > 0:
            res += ones[h] + " Hundred"
            if rem > 0:
                res += " and " + two_digits(rem)
        else:
            res += two_digits(rem)
        return res.strip()

    # Split into Crore, Lakh, Thousand, Hundred/Tens
    crore = integer_part // 10000000
    rem = integer_part % 10000000

    lakh = rem // 100000
    rem = rem % 100000

    thousand = rem // 1000
    rem = rem % 1000

    hundreds = rem

    parts = []
    if crore > 0:
        parts.append(two_digits(crore) + " Crore")
    if lakh > 0:
        parts.append(two_digits(lakh) + " Lakh")
    if thousand > 0:
        parts.append(two_digits(thousand) + " Thousand")
    if hundreds > 0:
        parts.append(three_digits(hundreds))

    words = " ".join(parts).strip()
    if not words:
        words = "Zero"

    res = f"Rupees {words}"
    if paisa_part > 0:
        res += f" and {two_digits(paisa_part)} Paise"
    res += " Only"
    return res

if __name__ == "__main__":
    print(number_to_indian_words(150000))
    print(number_to_indian_words(2548750.50))
    print(number_to_indian_words(8500))
