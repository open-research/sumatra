from sumatra.projects import init_websettings

NbCol = 14 # default number of columns

def initSettings(project, option='web'):
    '''Checking existence of the specific settings in .smt/project.
    In case it doesn't exist, it will be initialized with some default values
    Inputs:
        project: project object,
        option: string.
    Output:
        web_settings: dictionary.
    '''
    if option == 'web':
        try:
            return project.web_settings
        except AttributeError:
            project.web_settings = init_websettings()   
            for key, item in project.web_settings.iteritems():
                if item:
                    project.web_settings[key] = item
            project.save()
            return project.web_settings
    else:
        pass

def renderColWidth(web_settings):
    '''For calculating the width of the columns. These values will be send to .css
    Maybe it should rather be done using javascript?'''
    rendered_width = {}
    if web_settings['table_HideColumns'] is not None:
        nbCols_actual = NbCol - len(web_settings['table_HideColumns'])
    else:
        nbCols_actual = NbCol
    rendered_width['head'] = '%s%s' %(90.0/nbCols_actual, '%') # all columns except 'Label' since it should have bigger width
    if (nbCols_actual > 10):
        rendered_width['label'] = '150px'
    else:
        rendered_width['label'] = head_width
    return rendered_width