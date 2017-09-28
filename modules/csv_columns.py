def column_headers():
    column_dict = {
        
        "language_preference": ["Language Preference", "preferred Language Of Participant",
                                "Prefer Language for SMS 1.Hindi, 2.English, 3.Gujarati", "Prefer Language for SMS"],
        "name": ["Name", "First Name Of Child To Be Vaccinated", "Name of Child", "Childs Name", "Child's Name"],
        "phone_number": ["Phone Number", "Mobile No of  Pregnant/ Mother/ Father",
                    "Mobile Number of Respondent Capture At End", "Mobile Number of Respondent", "Primary Mobile"],
        "alt_phone_number": ["Alternative Phone", "Alternate Mobile Number", "Alternate Mobile No.", "Alternate Mobile No"],
        "delay_in_days": ["Delay in days"],
        "date_of_sign_up": ["Date of Sign Up", "Date of Survey (dd/mm/yy)", "Date of Survey"],
        "date_of_birth": ["Date of Birth", "Date Of Birth Of The Child",
                            "Date of Birth of Child (dd/mm/yyyy)", "Date of Birth of Child"],
        "functional_date_of_birth": ["Functional DoB"],

        # Personal Info
        "gender": ["Gender", "Gender Of Child", "Gender Of The Child"],
        "mother_tongue": ["Mother Tongue", "Mother Tongue Of Participant",
                            "Mother/Father Tongue 1.(Hindi, 2.English, 3.Other ", "Mother/Father Tongue"],
        "religion": ["Religion"],
        "state": ["State", "Name of State"],
        "division": ["Division", "Name of Division"],
        "district": ["District", "Name of District"],
        "city": ["City", "Center", "Name of District"],
        "monthly_income_rupees": ["Monthly Income"],
        "children_previously_vaccinated": ["Previously had children vaccinated", "Missed any Vaccination"],
        "not_vaccinated_why": ["If not vaccinated why"],
        "mother_first_name": ["Mother's First", "Name Of The Mother",
            "Name of Parents/Female Member of HH/Pregnant or Mother of child", "Mothers Name", "Mother's Name"],
        "mother_last_name": ["Mother's Last"],

        # Type of Sign Up
        "method_of_sign_up": ["Method of Sign Up"],
        "org_sign_up": ["Org Sign Up"],
        "hospital_name": ["Hospital Name"],
        "doctor_name": ["Doctor Name"],
        "preg_signup": ["Pregnant Signup", "Pregnant women  Yes=1, No=2", "Segment", "Pregnant women"],
        "month_of_pregnancy": ["Current Month Of Pregnancy", "Month of Pregnancy"],

        # System Identification
        "telerivet_contact_id": ["Telerivet Contact ID", "Contact ID"],
        "trial_id": ["Trial ID"],
        "trial_group": ["Trial Group"],

        # Message References
        "preferred_time": ["Preferred Time"],
        "script_selection": ["Script Selection"],
        "telerivet_sender_phone": ["Sender Phone"],
        "last_heard_from": ["Last Heard From"],
        "last_contacted": ["Last Contacted"],
        "time_created": ["Time Created"]
    }
    return column_dict


    