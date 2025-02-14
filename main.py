import xml.etree.ElementTree as ElementTree


# Parses time, given in format (something + 'T%H:%M:%S.' + something_else).
# Returns number of seconds since 00:00:00.
def get_time(string):
    time = string[string.find('T') + 1: string.find('.')].split(sep=':')
    return int(time[0]) * 60 * 60 + int(time[1]) * 60 + int(time[2])


MIN_COMMENTS = 15                           # Number of comments user need to have to get into our list.
SUNSET = get_time('T' + '00:00:00' + '.')   # Time, when night begins.
SUNRISE = get_time('T' + '05:00:00' + '.')  # Time, when night ends.
THRESHOLD = 0.5                             # How much the value night_comments/all_comments must be so user could get
                                            # into our list.
COMMENTS_FILE_NAME = 'Comments.xml'         # Name of file with comment data.
USERS_FILE_NAME = 'Users.xml'               # Name of file with user data.
RESULTS_FILE_NAME = 'results.htm'           # Name of file in which results will be writtens.


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
        self.identifier = int(xml_element.attrib['Id'])
        self.reputation = int(xml_element.attrib['Reputation'])
        self.creation_date = xml_element.attrib['CreationDate']
        self.creation_date = self.creation_date[0:self.creation_date.find('T')].replace('-', '.')
        self.display_name = xml_element.attrib['DisplayName']
        self.views = int(xml_element.attrib['Views'])

    def __repr__(self):
        return repr((self.identifier, self.display_name))

    # Generates HTML code of row, which will contain information about this user.
    def get_row(self, num, rev):
        return '<tr><td>' + str(num) + '</td>' \
               '<td><a href = "https://apple.stackexchange.com/users/' + str(self.identifier) + '">' \
               '' + self.display_name + '</a></td>' \
               '<td>' + self.creation_date + '</td>' \
               '<td>' + str(self.reputation) + '</td>' \
               '<td>' + str(self.views) + '</td>' \
               '<td>' + str(round(rev * 100, 1)) + '%</td></tr>'


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
user_ids = sorted(user_ids, key=lambda x: -x[1])    # Sorting by relevance.

root = ElementTree.parse(USERS_FILE_NAME).getroot()

users_by_id = dict()                                # Key - ID of user, value - User object.
for user in root.iter('row'):
    users_by_id[int(user.attrib['Id'])] = User(user)

rows = ''                                           # Generating HTML.
for i in range(0, len(user_ids)):
    rows += users_by_id[user_ids[i][0]].get_row(i + 1, user_ids[i][1])

header = '<!DOCTYPE style PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">' \
         '<html><head><title>Results</title><link rel="stylesheet" href="style.css"></head><body><table><thead><tr>' \
         '<td>No.</td><td>Username</td><td>Date</td><td>Reputation</td><td>Views</td><td>Relevance</td></tr>' \
         '</thead><tbody>'

footer = '</tbody></table></body></html>'

file = open(RESULTS_FILE_NAME, 'w')                 # Writing the results.
file.write(header + rows + footer)
file.close()