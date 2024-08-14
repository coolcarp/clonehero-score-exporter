import json
import datetime

# CH uses little endian
def to_int(bytes):
    return int.from_bytes(bytes, "little")
    
    
def write_to_csv(csv, values, offset=0):
    csv.write("," * offset + ",".join("\"" + str(value).replace("\"","\"\"") + "\"" for value in values) + "\n")
    

def safe_open(filename):
    try: 
        bin = open(filename, "rb")
    except FileNotFoundError:
        input(f"Make sure {filename} is in the same directory as this file.")
        return None 
    else:
        return bin


def get_difficulty(index):
    lookup = ["easy", "medium", "hard", "expert"]
    return lookup[index]


def get_instrument(index):
    # TODO: full list 
    lookup = ["lead", "bass", "rhythm", "3", "4", "5", "6", "keys"]
    return lookup[index] if index < len(lookup) else str(index) 


def handle_instrument(bin, info_dict, checksum):
    # The next 2 bytes should identify the instrument 
    instrument = get_instrument( to_int( bin.read(2) ) )
    # The next byte is the difficulty 
    difficulty = get_difficulty( to_int( bin.read(1) ) )
    # The next 2 bytes is the percentage numerator
    numerator = to_int( bin.read(2) )
    # The next 2 bytes is the percentage denominator
    denominator = to_int( bin.read(2) )
    # The next byte is the number of stars 
    num_stars = to_int( bin.read(1) )
    # The next 4 bytes make the number 1 
    bin.read(4)
    # The next 4 bytes is the score 
    score = to_int( bin.read(4) )
    # Write this data to the output 
    info_dict[checksum]["instruments"][instrument] = {
        "difficulty": difficulty,
        "percentage": numerator, 
        "stars": num_stars,
        "score": score
    }
    #write_to_csv(csv, [checksum, instrument, difficulty, numerator, num_stars, score])
    
    
def handle_song(bin, info_dict):
    # First 16 bytes are MD5 hash of notes.mid of song
    checksum = str(bin.read(16).hex())
    # Next byte is the number of instruments that have scores 
    num_scores = to_int( bin.read(1) )
    # The next bytes are the number of plays (unknown how long, 2-4)
    info_dict[checksum]["plays"] = to_int( bin.read(3) )
    # Initialize instruments dictionary 
    info_dict[checksum]["instruments"] = {}
    for instrument in range(num_scores):
        handle_instrument(bin, info_dict, checksum)


# Score data will be added to info_dict, and a CSV will be made
def handle_scores(info_dict):
    bin = safe_open("scoredata.bin")
    # First 4 bytes are some sort of header (i think) 
    header = bin.read(4) 
    # The next 4 bytes is the number of songs that have scores 
    num_songs_played = to_int( bin.read(4) ) 
    # Now, look through all the songs, making rows for each instrument
    for song in range(num_songs_played): 
        handle_song(bin, info_dict)   
    # Close files
    bin.close()


# If the first byte is >=128, then the next byte also contains length data (possibly recursive). 
def get_real_length(bin):
    length = to_int( bin.read(1) )
    if length >= 128:
        length += (to_int( bin.read(1) ) - 1) * 128
    return length


# Gets the next n bytes given the first one or two bytes. 
def get_string(bin):
    length = get_real_length(bin)
    string = bin.read(length).decode()
    return string 


def handle_lists(bin, num):
    lookup = [None] * num
    for i in range(num):
        lookup[i] = get_string(bin)
    return lookup


def get_metalist():
    return ["Title", "Artist", "Album", "Genre", "Year", "Charter", "Playlist"]


# Return the metadata of each song based on checksum. Indexes are converted. 
def handle_metadata(bin, lookups, num):
    order = get_metalist()
    info_dict = {}
    for i in range(num):
        # Filepath 
        get_string(bin)
        # Unknown checksum (?) 
        bin.read(16) 
        # File name 
        get_string(bin)
        # Delim (?)
        bin.read(1)
        # Metadata (title, artist...)
        metadata = {}
        for category in order: 
            # Convert the index to the string 
            metadata[category] = lookups[category][to_int( bin.read(4) )]
        # (?)
        bin.read(8) 
        # Difficulties of instruments (?)
        bin.read(13) 
        # Start offset 
        bin.read(4) 
        # Icon 
        get_string(bin)
        # (?)
        bin.read(8)
        # Song time (miliseconds)
        metadata["songlength"] = to_int( bin.read(4) )
        # (?)
        bin.read(8)
        # Game (?) 
        get_string(bin)
        # Delim (?)
        bin.read(1)
        # Checksum of file 
        checksum = str(bin.read(16).hex())
        info_dict[checksum] = metadata
    return info_dict


# Returns the lookup dictionary and info for each song. With both of these, you can get any attribute of any checksum. 
def handle_cache():
    bin = safe_open("songcache.bin")
    # Has a header of length 20 (?)
    bin.seek(20)
    # Stored in this order
    order = get_metalist()
    # Extract each of the cached data 
    lookups = {}
    for category in order: 
        bin.read(1) # Skip the marker 
        lookups[category] = handle_lists(bin, to_int( bin.read(4) ))
    # Checksum stored slightly differently 
    info_dict = handle_metadata(bin, lookups, to_int( bin.read(4) ))
    # Create the CSV 
    #for checksum in info_dict:
    #    write_to_csv(csv, [info_dict[checksum][category] for category in info_dict[checksum]])
    # Close files
    bin.close()
    return info_dict


# Get rid of scoreless entries 
def trim_info(info_dict):
    for checksum in list(info_dict):
        if not "instruments" in info_dict[checksum]:
            del info_dict[checksum]


def handle_json(info_dict):
    json_string = json.dumps(info_dict, indent="\t")
    json_file = open("scores.json", "w", encoding="utf-8")
    json_file.write(json_string)
    json_file.close()


def handle_csv(info_dict):
    csv = open("scores.csv", "w", encoding="utf-8")
    write_to_csv(csv, ["Checksum", "Title", "Artist", "Charter", "songlength", "plays", "instrument", "difficulty", "percentage", "stars", "score"])
    for checksum in info_dict:
        info = info_dict[checksum]
        write_to_csv(csv, [checksum, info["Title"], info["Artist"], info["Charter"], info["songlength"], info["plays"]])
        for instrument in info["instruments"]:
            instrument_info = info["instruments"][instrument]
            write_to_csv(csv, [instrument, instrument_info["difficulty"], instrument_info["percentage"], instrument_info["stars"], instrument_info["score"]], 6)
    csv.close()

def get_playtime(info_dict):
    sum = 0
    for checksum in info_dict:
        sum += info_dict[checksum]["plays"] * info_dict[checksum]["songlength"] / 1000
    return sum 


def main():
    # Figure out the titles that correspond with checksums 
    print("Parsing cache")
    info_dict = handle_cache()
    # Now make the main CSV 
    print("Parsing scores")
    handle_scores(info_dict)
    # Trim the data 
    trim_info(info_dict)
    # JSON 
    print("Creating json")
    handle_json(info_dict)
    # CSV 
    print("Creating CSV")
    handle_csv(info_dict)
    # Playtime
    print(f"Playtime: {datetime.timedelta(seconds=get_playtime(info_dict))}")


if __name__ == "__main__":
    main()
