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

def createLangList():
  res = ''
  for k in langKeys:
    res = res + '\n' + f'**{k}**: {langCodes[k]}'
  return res

langKeys = langCodes.keys()
langList = createLangList()

def helpMsg(botId):
  return f'''Hello, I am a translate chatbot. Please reply "@![:Person]({botId}) **[sourceLangCode]>[targetLangCode] [xxxxxx]**" if you want to translate something.

**Example**

@![:Person]({botId}) **en>fr Hello world**

Or use auto detect

@![:Person]({botId}) **>fr Hello world**

You can read about supported language code from [aws translate document](https://docs.aws.amazon.com/translate/latest/dg/API_TranslateText.html) or use "**@![:Person]({botId}) langs**"

  '''


def botJoinPrivateChatAction(bot, groupId, user, dbAction):
  """
  bot join private chat event handler
  bot could send some welcome message or help, or something else
  """
  text = helpMsg(bot.id)
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

  msg = helpMsg(bot.id)
  langErr = f'''You can only choose language code from this list:

{langList}
  '''
  m = re.match(r'.+ +langs', text)
  if not m is None:
    return bot.sendMessage(
      groupId,
      {
        'text': langErr
      }
    )

  m = re.match(r'.+ ([\w-]+)?>([\w-]+) (.+)', text)
  if m is None:
    bot.sendMessage(
      groupId,
      {
        'text': msg
      }
    )
    return

  src = m.group(1)
  tar = m.group(2)
  txt = m.group(3)

  if (not src is None and not src in langKeys) or not tar in langKeys:
    bot.sendMessage(
      groupId,
      {
        'text': langErr
      }
    )
    return

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

  final = f'''![:Person]({creatorId}) Translate result:

  **{transCodeSrc}: {langCodes[transCodeSrc]}** > **{transCodeTar}: {langCodes[transCodeTar]}**

  **{trans}**


> {txt}
  '''

  print('TranslatedText: ' + trans)
  print('SourceLanguageCode: ' + transCodeSrc)
  print('TargetLanguageCode: ' + transCodeTar)

  return bot.sendMessage(
    groupId,
    {
      'text': final
    }
  )

