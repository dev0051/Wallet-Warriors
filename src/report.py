def generate_report(probability):

    if probability > 0.6:
        decision = "Reject"
    else:
        decision = "Approve"

    print("Loan Decision Report")
    print("---------------------")
    print("Default Probability:", probability)
    print("Decision:", decision)