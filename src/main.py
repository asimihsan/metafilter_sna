#!/usr/bin/env python

import tasks

def main():
    # -------------------------------------------------------------------------
    #   !!AI Make this configurable but drop the database.
    # -------------------------------------------------------------------------
    tasks.drop_database.delay().get()
    # -------------------------------------------------------------------------

    tasks.initialize_database.delay().get()
    tasks.get_post_uris.delay()

if __name__ == "__main__":
    main()


