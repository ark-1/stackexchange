import xml.etree.ElementTree as ElementTree


# Parses time, given in format (something + 'T%H:%M:%S.' + something_else).
# Returns number of seconds since 00:00:00.
def get_time(string):
    time = string[string.find('T') + 1: string.find('.')].split(sep=':')
    return int(time[0]) * 60 * 60 + int(time[1]) * 60 + int(time[2])


MIN_COMMENTS = 15                           # Number of comments user need to have to get into our list.
SUNSET = get_time('T' + '00:00:00' + '.')   # Time, when night begins.
SUNRISE = get_time('T' + '05:00:00' + '.')  # Time, when night ends.
THRESHOLD = 0                               # How much the value night_comments/all_comments must be so user could get
                                            # into our list.
COMMENTS_FILE_NAME = 'Comments.xml'         # Name of file with comment data.
USERS_FILE_NAME = 'Users.xml'               # Name of file with user data.


def compare(a, b):
    if a > b:
        return 1
    if a < b:
        return -1
    return 0


# Checks if this time (in seconds since the start of the day) is at night.
def nighttime(t):
    return compare(t, SUNSET) * compare(t, SUNRISE) * compare(SUNSET, SUNRISE) >= 0


class User:
    def __init__(self, xml_element):
        self.id = int(xml_element.attrib['Id'])
        self.reputation = int(xml_element.attrib['Reputation'])
        self.creation_date = xml_element.attrib['CreationDate']
        self.display_name = xml_element.attrib['DisplayName']
        self.views = int(xml_element.attrib['Views'])

    def __repr__(self):
        return repr((self.id, self.display_name))


root = ElementTree.parse(COMMENTS_FILE_NAME).getroot()

comments_by_user = dict()               # Key - ID of user, value - set of comments.
for comment in root.iter('row'):
    user = comment.attrib.get('UserId')
    if user is None:                    # If user has no ID, we skip him. We don't want unregistered users in out list.
        continue
    user = int(user)
    if comments_by_user.get(user) is None:
        comments_by_user[user] = []
    comments_by_user[user].append(comment.attrib)

user_ids = list()                       # List of tuples, containing the IDs of users that will get into our list and
                                        # the value (night_comments / all comments). It's our relevance criterion.
for user in comments_by_user.keys():
    if len(comments_by_user[user]) >= MIN_COMMENTS:
        night_comments = 0
        for comment in comments_by_user[user]:
            if nighttime(get_time(comment['CreationDate'])):
                night_comments += 1
        if night_comments / len(comments_by_user[user]) >= THRESHOLD:
            user_ids.append((user, night_comments / len(comments_by_user[user])))
user_ids = sorted(user_ids, key=lambda x: x[1])     # Sorting by relevance, just for fun.

root = ElementTree.parse(USERS_FILE_NAME).getroot()

users_by_id = dict()                                # Key - ID of user, value - User object.
for user in root.iter('row'):
    users_by_id[int(user.attrib['Id'])] = User(user)
for identifier in user_ids:                         # Printing our list, just for fun.
    print(users_by_id[identifier[0]], identifier[1])
