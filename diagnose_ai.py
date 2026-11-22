import sys, traceback, importlib.util
print('Python:',sys.version)
print('Executable:',sys.executable)
for name in ('PIL','rembg','onnxruntime','cv2','numpy'):
    try:
        spec=importlib.util.find_spec(name)
        print(name, 'FOUND' if spec else 'MISSING')
    except Exception as e: print(name, repr(e))
try:
    from rembg import new_session
    print('Initializing u2netp model (may download on first run)...')
    new_session('u2netp')
    print('SUCCESS: AI model initialized')
except Exception:
    print('MODEL INITIALIZATION FAILED:')
    traceback.print_exc()
