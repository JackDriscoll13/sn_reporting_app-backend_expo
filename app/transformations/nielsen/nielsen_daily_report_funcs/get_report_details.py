from crud import nielsen_crud

def get_subject_line_ids(db):
    """
    Get the subject line ids from the database.
    """
    result = nielsen_crud.get_subject_lines_as_dataframe(db)
    return result['id'].to_list()


def get_subject_lines(db):
    """
    Get the subject lines from the database.
    """
    result = nielsen_crud.get_subject_lines_as_dataframe(db)
    emailsubjects = result['subject'].to_list()
    return emailsubjects


def get_report_notes(db, ids:list): 
    """
    Get the report notes from the database.
    """
    results = []
    for id in ids:
        result = nielsen_crud.get_report_notes_as_dataframe(db, id)
        results.append(result['note'].to_list()[0]) # We only have one note per subject line, we flatten the list with the first element
    return results

def get_report_recipients(db, ids:list):
    """
    Get the report recipients from the database.
    """
    results = []
    for id in ids:
        result = nielsen_crud.get_report_recipients_as_dataframe(db, id)
        results.append(result['email'].to_list())
    return results

def get_report_dma_lists(db, ids:list):
    """
    Get the report dma lists from the database.
    """
    results = []
    for id in ids:
        result = nielsen_crud.get_report_dma_lists_as_dataframe(db, id)
        results.append(result['dma'].to_list())
    return results



