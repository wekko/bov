import aiohttp


from plugin_system import Plugin
plugin = Plugin('Голос', usage="скажи [выражение] - бот сформирует "
                               "голосовое сообщение на основе текста")
try:
    from gtts import gTTS
    import langdetect
except ImportError:
    plugin.log('gTTS или langdetect не установлены, плагин Голос не будет работать')
    gTTS = None
    langdetect = None
FAIL_MSG = 'Я не смог это произнести :('
@plugin.on_command('скажи')
async def say_text(msg, args):
    if not gTTS or not langdetect:
        return await msg.answer('Я не могу говорить, '
                                'так как у меня не хватает модулей :(')

    text = ' '.join(args)
    try:
        # Используется Google Text To Speech и библиотека langdetect
        lang = langdetect.detect(text)
        if lang == 'mk':
            # Иногда langdetect детектит русский как македонский
            lang = 'ru'
        tts = gTTS(text=text, lang=lang)
    except Exception as ex:
        # На самом деле не все языки, которых нет в gTTS, не поддерживаются
        # Например, gTTS считает, что GTTS не поддерживает украинский, хотя он поддерживает
        if 'Language' in ex:
            return await msg.answer('Данный язык не поддерживается.'
                                    'Если вы считаете, что он должен поддерживаться,'
                                    'напишите администратору бота!')
        raise # Если эта ошибка не связана с gTTS, бросаем её ещё раз

    # Сохраняем файл с голосом
    tts.save('audio.mp3')
    # Получаем URL для загрузки аудио сообщения
    upload_server = await msg.vk.method('docs.getUploadServer', {'type':'audio_message'})
    url = upload_server.get('upload_url')
    if not url:
        return await msg.answer(FAIL_MSG)

    # Загружаем аудио через aiohttp
    form_data = aiohttp.FormData()
    form_data.add_field('file', open('audio.mp3', 'rb'))
    async with aiohttp.post(url, data=form_data) as resp:
        file_url = await resp.json()
        file = file_url.get('file')
        if not file:
            return await msg.answer(FAIL_MSG)

    # Сохраняем файл в документы (чтобы можно было прикрепить к сообщению)
    saved_data = await msg.vk.method('docs.save', {'file':file} )

    # Получаем первый элемент, так как мы сохранили 1 файл
    media = saved_data[0]
    media_id, owner_id = media['id'], media['owner_id']
    # Прикрепляем аудио к сообщению :)
    await msg.answer('', attachment=f'doc{owner_id}_{media_id}')