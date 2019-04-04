"""
sample config module
run "cp config.sample.py config.py" to create local config
edit config.py functions to override default bot behavior
"""
import boto3
import re
import os

__name__ = 'localConfig'
__package__ = 'ringcentral_bot_framework'

region = 'us-east-1'
try:
  region = os.environ['AWS_REGION']
except:
  pass

langCodes = {
  'ar': 'Arabic',
  'zh': 'Chinese (Simplified)',
  'zh-TW': 'Chinese (Traditional)',
  'cs': 'Czech',
  'da': 'Danish',
  'nl': 'Dutch',
  'en': 'English',
  'fi': 'Finnish',
  'fr': 'French',
  'de': 'German',
  'he': 'Hebrew',
  'id': 'Indonesian',
  'it': 'Italian',
  'ja': 'Japanese',
  'ko': 'Korean',
  'pl': 'Polish',
  'pt': 'Portuguese',
  'ru': 'Russian',
  'es': 'Spanish',
  'sv': 'Swedish',
  'tr': 'Turkish'
}

botName = 'translate-bot'

def defaultLang():
  return 'English[en]'

def createLangList():
  res = ''
  for k in langKeys:
    res = res + '\n' + f'**{k}**: {langCodes[k]}'
  return res

langKeys = langCodes.keys()
langList = createLangList()

def helpMsg(botId, defaultLang):
  return f'''Hello, I am a translate chatbot. Please reply "![:Person]({botId}) **[sourceLangCode]>[targetLangCode] [xxxxxx]**" if you want to translate something.

**Example**

![:Person]({botId}) **en>fr Hello world**

Or use auto detect

![:Person]({botId}) **>fr Hello world**

Or auto translate to **default language: {defaultLang}**

![:Person]({botId}) Hello world**

You can also set default language by post **![:Person]({botId}) set [langCode]**

You can read about supported language code from [aws translate document](https://docs.aws.amazon.com/translate/latest/dg/API_TranslateText.html) or post "**![:Person]({botId}) langs**"

  '''

def botJoinPrivateChatAction(bot, groupId, user, dbAction):
  """
  bot join private chat event handler
  bot could send some welcome message or help, or something else
  """
  text = helpMsg(bot.id, defaultLang())
  bot.sendMessage(
    groupId,
    {
      'text': text
    }
  )

def botGotPostAddAction(
  bot,
  groupId,
  creatorId,
  user,
  text,
  dbAction,
  handledByExtension,
  event
):
  """
  bot got group chat message: text
  bot could send some response
  """
  if not f'![:Person]({bot.id})' in text or handledByExtension:
    return

  langErr = f'''You can only choose language code from this list:

{langList}
  '''
  def sendMsg(msg):
    bot.sendMessage(
      groupId,
      {
        'text': msg
      }
    )
  where = {
    'id': f'{bot.id}_{groupId}_{botName}'
  }
  inst = dbAction('user', 'get', where)
  defaultLangStr = defaultLang()
  defaultLangCode = 'en'
  if not inst == False:
    defaultLangStr = inst['data']['defaultLangStr']
    defaultLangCode = inst['data']['defaultLangCode']
  msg = helpMsg(bot.id, defaultLangStr)
  print('defaultLangStr', defaultLangStr)
  print('defaultLangCode', defaultLangCode)

  # no content
  m1 = re.match(r'[^ ]+ *$', text)
  if not m1 is None:
    return sendMsg(msg)

  # set default language
  m2 = re.match(r'[^ ]+ +set +(.+)', text)
  if not m2 is None:
    tar = m2.group(1)
    if not tar in langCodes:
      return sendMsg(f'''{tar} not in supported language list.
{langErr}
''')
    langName = langCodes[tar]
    defaultLangStr0 = f'{langName}[{tar}]'
    if not inst == False:
      dbAction('user', 'update', {
        'id': where['id'],
        'update': {
          'data': {
            'defaultLangStr': defaultLangStr0,
            'defaultLangCode': tar
          }
        }
      })
    else:
      dbAction('user', 'add', {
        'id': where['id'],
        'data': {
          'defaultLangStr': defaultLangStr0,
          'defaultLangCode': tar
        }
      })
    return sendMsg(f'Default language set to [{tar}]')

  # list langs
  m = re.match(r'[^ ]+ +langs', text)
  if not m is None:
    return sendMsg(langErr)

  # translate with target language
  m = re.match(r'[^ ]+ ([\w-]+)?>([\w-]+) (.+)', text)
  src = None
  tar = ''
  txt = ''
  if m is None:
    m3 = re.match(r'[^ ]+ +(.+)', text)
    txt = m3.group(1)
    tar = defaultLangCode
  else:
    src = m.group(1)
    tar = m.group(2)
    txt = m.group(3)

  if (not src is None and not src in langKeys) or not tar in langKeys:
    sendMsg(langErr)
    return

  try:
    translate = boto3.client(
      service_name='translate',
      region_name=region,
      use_ssl=True
    )
    result = translate.translate_text(
      Text=txt,
      SourceLanguageCode=src or 'auto',
      TargetLanguageCode=tar
    )
    trans = result.get('TranslatedText') or ''
    transCodeSrc = result.get('SourceLanguageCode') or 'unknown'
    transCodeTar = result.get('TargetLanguageCode') or 'unknown'

    final = f'''![:Person]({creatorId}) says:
**{trans}**

**{transCodeSrc}: {langCodes[transCodeSrc]}** > **{transCodeTar}: {langCodes[transCodeTar]}**
> {txt}'''

    print('TranslatedText: ' + trans)
    print('SourceLanguageCode: ' + transCodeSrc)
    print('TargetLanguageCode: ' + transCodeTar)

    sendMsg(final)
  except:
    sendMsg('Translate fails :thinking:')

