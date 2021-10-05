datasets = {}

'''
Reports is a list of dicts, with dicts like:
d = {
    'vname': 'view name', # e.g. U-Pb Concordia 
    'rname': 'report name', # e.g. Discordia age
    'time': time_stamp, # ...
    'text': content, # ...
    'dataset': dsname # My zircon
}
'''
reports = []