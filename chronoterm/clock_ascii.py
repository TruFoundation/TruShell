def clock_ascii(clock_text, template_type):
    
    if template_type == "wrist_watch":
        template1 = """
             ___
            |---|
            |_|_|
            |   |
            |   |
            |   |
            |   |
            |   |
            |___|
           /_____\\
           |HH:MM|
           |_____|
           |.....|
           \ ___ /
            |   |
            |   |
            |   |
            | . |
            | . |
            | . | 
            | . |
            | . |
            | . |
            | . |
            | . |
            |___|

        """
        clock_ascii = template1.replace("HH:MM", clock_text)

        return clock_ascii


    elif template_type == "lcd":
        template2 = """
             ___________________
            |  _______________  |
            | |     HH:MM     | |
            | |_______________| |
            |  ___ ___ ___ ___  |
            |_|___|___|___|___|_|
        """

        clock_ascii = template2.replace("HH:MM", clock_text)

        return clock_ascii


    elif template_type == "desktop":
        template3 = """
            _____________________
            |                     |
            |        HH:MM        |
            |                     |
            |_____________________|
                    |   |
                ____|___|____
                |_____________|
        """
        clock_ascii = template3.replace("HH:MM", clock_text)

        return clock_ascii
