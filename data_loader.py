import pandas as pd

def load_data_from_csv():
    try:
        global_admin = pd.read_csv('Database/global_admin.csv', encoding='ISO-8859-1')
        local_admin_1 = pd.read_csv('Database/local_admin_institute_1.csv', encoding='ISO-8859-1')
        local_admin_2 = pd.read_csv('Database/local_admin_institute_2.csv', encoding='ISO-8859-1')
        student_data_1 = pd.read_csv('Database/student_data_institute_1.csv', encoding='ISO-8859-1')
        student_data_2 = pd.read_csv('Database/student_data_institute_2.csv', encoding='ISO-8859-1')
        polls_1 = pd.read_csv('Database/polls_institute_1.csv', encoding='ISO-8859-1')
        polls_2 = pd.read_csv('Database/polls_institute_2.csv', encoding='ISO-8859-1')

        return (global_admin, local_admin_1, local_admin_2, student_data_1, student_data_2, polls_1, polls_2)

    except Exception as e:
        raise ValueError(f"Error parsing one or more CSV files: {e}")
