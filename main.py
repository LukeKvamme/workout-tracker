from app import create_app

app = create_app()

if __name__ == '__main__': # only if we run THIS file, not IMPORT-ing. Only run web server if you import create_app directly
    app.run(debug=True) #debug=T >> automatically rerun web server every time there is a new change made
