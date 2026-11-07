// 輔具預約「welfare」區的介面文字。key 一律以 `welfare.` 開頭。
// 九個題目、福利項目名稱與各項目詳細頁是官方原文，不放在這裡（英文介面維持中文並標 lang="zh-TW"）。
export const zh: Record<string, string> = {
  'welfare.title': '輔具福利查詢',
  'welfare.intro.title': '友善提醒',
  'welfare.introText':
    '您好，以下請您針對輔具需求者的狀況進行問答(共有5~10題)，將根據問答結果，提供您相關之福利資訊。',
  'welfare.start': '開始填答',
  'welfare.question': '問題{n}',
  'welfare.prev': '上一題',
  'welfare.next': '下一題',
  'welfare.viewResult': '觀看結果',
  'welfare.restart': '重新填答',
  'welfare.result.title': '問答結果',
  'welfare.result.lead': '您可能符合以下補助項目，請點選各項目名稱以獲得更多資訊：',
  'welfare.result.empty.title': '依您的回答，查無可能符合的補助項目',
  'welfare.result.empty.hint': '如需諮詢輔具相關福利，請洽您所在行政區的輔具中心。',
  'welfare.result.sep': '、',
  'welfare.error.number': '請輸入數字!',
  'welfare.error.positive': '請輸入大於0的數字!',
  'welfare.error.choose': '請選擇',
  'welfare.notFound': '找不到這個項目'
};
export const en: Record<string, string> = {
  'welfare.title': 'Assistive device benefits lookup',
  'welfare.intro.title': 'Friendly reminder',
  'welfare.introText':
    'Please answer a few questions (5 to 10 in total) about the situation of the person who needs assistive devices. Based on your answers, we will show you the benefits that may apply.',
  'welfare.start': 'Start',
  'welfare.question': 'Question {n}',
  'welfare.prev': 'Previous',
  'welfare.next': 'Next',
  'welfare.viewResult': 'View results',
  'welfare.restart': 'Start over',
  'welfare.result.title': 'Results',
  'welfare.result.lead':
    'You may qualify for the following subsidies; select an item name for more information:',
  'welfare.result.empty.title': 'No subsidies match your answers',
  'welfare.result.empty.hint':
    'For advice on assistive device benefits, please contact the assistive device center for your district.',
  'welfare.result.sep': ', ',
  'welfare.error.number': 'Please enter a number.',
  'welfare.error.positive': 'Please enter 0 or a larger number.',
  'welfare.error.choose': 'Please select an option.',
  'welfare.notFound': 'Item not found'
};
