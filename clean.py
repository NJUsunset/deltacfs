import shutil

if __name__ == '__main__':
    print('INFO: clean.py running...')
    
    # Clean up temporary directories
    shutil.rmtree('temp/', ignore_errors=True)
    shutil.rmtree('output/', ignore_errors=True)
    shutil.rmtree('logs/', ignore_errors=True)
    shutil.rmtree('output.log', ignore_errors=True)
    
    print('INFO: clean.py finished.')