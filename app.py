import os
import sys
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_restx import Api, Resource, fields
# from flask_wtf.csrf import CSRFProtect
from nltk.tokenize import sent_tokenize, word_tokenize

import nltk
nltk.download('punkt')


import pymongo
def get_collection():
    # Get connection info from environment variables
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    DB_NAME = os.getenv('DB_NAME')
    COLLECTION_NAME = os.getenv('COLLECTION_NAME')
    
    # Create a MongoClient
    client = pymongo.MongoClient(CONNECTION_STRING)
    try:
        client.server_info() # validate connection string
    except pymongo.errors.ServerSelectionTimeoutError:
        raise TimeoutError("Invalid API for MongoDB connection string or timed out when attempting to connect")

    db = client[DB_NAME]
    return db[COLLECTION_NAME]



application = Flask(__name__)

# if not 'WEBSITE_HOSTNAME' in os.environ:
#    # local development, where we'll use environment variables
#    print("Loading config.development.")
#    app.config.from_object('azureproject.development')
# else:
#    # production
#    print("Loading config.production.")
#    app.config.from_object('azureproject.production')

app = Api(app=application,
          version="1.0",
          title="ReWARD",
          description="Record Writer Actions for Rhetorical Adjustments")

name_space = app.namespace('ReWARD', description='Record writing activity')
model = app.model('Recording Writer Actions for Rhetorical Adjustment',
                  {'Reward': fields.String(required=True,
                                         description="--",
                                         help="--")})
db = get_collection()

check = 0
@name_space.route("/activity")
class MainClass(Resource):
    
    check = 0
    @app.doc(responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error'},
             params={'activity': 'data from most recent writing activity',
                     'timestamp': 'The time at which writer action was recorded'})
    def get(self):
        try:
            summary = "retrieving the writing actions real time from user input into the overleaf editor"
            # resp_json = request.get_data()
            # print(resp_json)

            return {
                "status": "Writer action's retrieved",
            }
        except KeyError as e:
            name_space.abort(500, e.__doc__, status="Could not retrieve information", statusCode="500")
        except Exception as e:
            name_space.abort(400, e.__doc__, status="Could not retrieve information", statusCode="400")

    @app.doc(responses={200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error'},
             params={'activity': 'data from most recent writing activity',
                     'timestamp': 'The time at which writer action was recorded'})
    @app.expect(model)
    def findback(self, i, type, skip, text):
        back = ""
        check = 0
        if (" " in text[i][1] or "\n" in text[i][1]) and (len(text[i][1]) > 1):
            return check, back
        for k in range(i + 1, len(text)):
            if text[k][0] == skip or len(text[k]) > 2:
                if text[k][0] == skip:
                    check = 1
                k += 1
            else:
                idx = text[k][1].find(" ")
                idx2 = text[k][1].find("\n")
                if idx > idx2 and (idx2 != -1):
                    idx = idx2
                if text[k][0] != 0:
                    text[k].append(1)
                if idx == 0:
                    if text[k][0] == type:
                        back += text[k][1]
                    return check, back
                else:
                    if idx == -1:
                        back += text[k][1]
                    else:
                        if text[k][0] == type:
                            back += text[k][1]
                        else:
                            back += text[k][1][:idx]
                        return check, back
        return check, back

    def findfront(self, i, skip, text):
        front = ""
        check = 0
        if (" " in text[i][1]) and (len(text[i][1]) > 1):
            return check, front
        for k in range(i - 1, -1, -1):
            if text[k][0] == skip:
                check = 1
                k -= 1
            else:
                if (text[k][1].rfind(" ") == (len(text[k][1]) - 1)) or (
                        text[k][1].rfind("\n") == (len(text[k][1]) - 1)):
                    return check, front
                elif (text[k][1].rfind(" ") != 0) or (text[k][1].rfind("\n") != 0):
                    idx2 = text[k][1].rfind(" ")
                    idx3 = text[k][1].rfind("\n")
                    if idx3 > idx2 and (idx2 != -1):
                        idx2 = idx3
                    if idx2 == -1:
                        front = text[k][1] + front
                    else:
                        front = text[k][1][idx2 + 1:] + front
                        return check, front
        return check, front

    def countChar(self, i, text):
        pos = 0
        if "\n" == text[i][1][0]:
            return pos
        for k in range(i - 1, -1, -1):
            if text[k][0] == -1:
                k -= 1
            else:
                idx = text[k][1].rfind("\n")
                if idx == (len(text[k][1]) - 1):
                    break
                elif idx == -1:
                    pos += len(text[k][1])
                else:
                    pos += len(text[k][1][idx + 1:])
                    break
        return pos

    def pasteCountChar(self, text, revision):
        i = 0
        pos = 0
        for j in range(len(text)):
            try:
                if text[i] != revision[i]:
                    i = j
                    break
            except IndexError:
                i = j
                break
        for k in range(i - 1, -1, -1):
            if text[k] == '\n':
                break
            pos += 1
        return pos

    def pasteHandler(self, info, pre, cur, order, lineNum):
        charNum = self.pasteCountChar(info["text"], info["revision"])
        i = 0
        list1 = []
        list2 = []
        list3 = []
        while i < len(cur):
            if i >= len(pre):
                list2.extend(cur[i:])
                break
            else:
                if pre[i] != cur[i]:
                    if pre[i] in cur[i:]:
                        list3.append(cur[i])
                        cur.pop(i)
                    else:
                        list1.append(pre[i])
                        list2.append(cur[i])
                        i += 1
                else:
                    if list3 != []:
                        if pre[i] == list3[0][0]:
                            list3.pop(0)
                    i += 1
        list2.extend(list3)
        start = ''
        end = ''
        if order == 1:
            if list1:
                for each in list1:
                    start = start + each + ' '
                for each in list2:
                    end = end + each + ' '
                info['changes'] = '(' + str(lineNum) + ',' + str(charNum) + ')' + ", " + start + "->" + end
            else:
                for each in list2:
                    end = end + each + ' '
                info['changes'] = '(' + str(lineNum) + ',' + str(charNum) + ')' + ", " + end + "---added"
        else:
            if list2:
                for each in list2:
                    start = start + each + ' '
                for each in list1:
                    end = end + each + ' '
                info['changes'] = '(' + str(lineNum) + ',' + str(charNum) + ')' + ", " + start + "->" + end
            else:
                for each in list1:
                    end = end + each + ' '
                info['changes'] = '(' + str(lineNum) + ',' + str(charNum) + ')' + ", " + end + "---added"
        info.pop("state")
        info["text"] = info.pop("revision")
        info["paste"] = info.pop("cb")
        return info

    def post(self):
        try:
            info = request.get_json(force=True)
            # db.activity.insert_one(info)
            state = info['state']
            lineNum = info['line']
            if state == 3:
                pre = []
                for s in info["text"].splitlines():
                    pre.extend(sent_tokenize(s))
                cur = []
                for s in info["revision"].splitlines():
                    cur.extend(sent_tokenize(s))
                pre = sent_tokenize(info["text"])
                cur = sent_tokenize(info["revision"])
                if len(pre) > len(cur):
                    info = self.pasteHandler(info, cur, pre, 2, lineNum)
                else:
                    info = self.pasteHandler(info, pre, cur, 1, lineNum)
                db.activity.insert_one(info)
                return {
                    "status": "Updated recent writing actions in doc",
                }
            text = info['revision']
            length = len(text)
            changes = []
            swapword = []
            index = 0
            for i in range(length):
                front = ""
                back = ""
                if len(text[i]) > 2 or text[i][0] != -1:
                    continue
                elif (text[i][0] == -1) and (0 < i < length - 1):
                    check2, front = self.findfront(i, 1, text)
                    check1, back = self.findback(i, -1, 1, text)
                    pos = self.countChar(i, text)
                    if check1 or check2:
                        swapword.append(
                            '(' + str(lineNum) + ',' + str(pos) + ')' + ", " + front + text[i][1] + back + "->")
                    elif front + back != "":
                        check2, front1 = self.findfront(i, -1, text)
                        check1, back1 = self.findback(i, -1, -1, text)
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + front + text[i][
                            1] + back + "->" + front1 + back1)
                    else:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")

                elif (text[i][0] == -1) and i == 0:
                    check1, back = self.findback(i, -1, 1, text)
                    pos = self.countChar(i, text)
                    if front + back != "":
                        check1, back1 = self.findback(i, -1, -1, text)
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + front + text[i][
                            1] + back + "->" + front + back1)
                    else:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")

                elif (text[i][0] == -1) and (i + 1 == length):
                    pos = self.countChar(i, text)
                    if " " in text[i][1]:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")
                    elif length == 1:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")
                    else:
                        check2, front = self.findfront(i, 1, text)
                        if front + back != "":
                            check2, front1 = self.findfront(i, -1, text)
                            changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + front1 + text[i][
                                1] + back + "->" + front + back)
                        else:
                            changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---deleted")

            for i in range(length):
                front = ""
                back = ""
                if len(text[i]) > 2 or text[i][0] != 1:
                    continue
                elif (text[i][0] == 1) and (0 < i < length - 1):
                    pos = self.countChar(i, text)
                    if i == length - 2 and (text[length - 1][1].isspace() or text[length - 1][1] == "\n"):
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
                    else:
                        check1, back = self.findback(i, 1, -1, text)
                        check2, front = self.findfront(i, -1, text)
                        if (check1 or check2) and (swapword != []):
                            swapword[index] += (front + text[i][1] + back)
                            changes.append(swapword[index])
                            index += 1
                        elif front + back != "":
                            check2, front1 = self.findfront(i, 1, text)
                            check1, back1 = self.findback(i, 1, 1, text)
                            changes.append(
                                '(' + str(lineNum) + ',' + str(pos) + ')' + ", " + front1 + back1 + "->" + front +
                                text[i][1] + back)
                        else:
                            changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")

                elif (text[i][0] == 1) and (i == 0):
                    check1, back = self.findback(i, 1, -1, text)
                    pos = self.countChar(i, text)
                    if front + back != "":
                        check1, back1 = self.findback(i, 1, 1, text)
                        changes.append(
                            '(' + str(lineNum) + ',' + str(pos) + ')' + ", " + front + back1 + "->" + front + text[i][
                                1] + back)
                    else:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
                elif (text[i][0] == 1) and (i + 1 == length):
                    pos = self.countChar(i, text)
                    if text[i][1][0] == " " or text[i][1][0] == "\n":
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
                    elif length == 1:
                        changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")
                    else:
                        check2, front = self.findfront(i, -1, text)
                        if front + back != "":
                            check1, back1 = self.findback(i, 1, 1, text)
                            changes.append(
                                '(' + str(lineNum) + ',' + str(pos) + ')' + ", " + front + back + "->" + front +
                                text[i][1] + back1)
                        else:
                            changes.append('(' + str(lineNum) + ',' + str(pos) + ')' + ", " + text[i][1] + "---added")

            info["changes"] = changes
            if state == 0:
              info.pop("state")
              info.pop("cb")
            elif state == 1:
              info.pop("state")
              info["cut"] = info.pop("cb")
            elif state == 2:
              info.pop('state')
              info["copy"] = info.pop("cb")
            db.activity.insert_one(info)
            # print(info)

            return {
                "status": "Updated recent writing actions in doc",
            }
        except KeyError as e:
            name_space.abort(500, e.__doc__, status="Could not save information", statusCode="500")
        except Exception as e:
            name_space.abort(400, e.__doc__, status="Could not save information", statusCode="400")

if __name__ == "__main__":
    app.run()
