// 輔具預約「borrow」區的介面文字。key 一律以 `borrow.` 開頭。
// 另外三個前綴也歸這裡：`center.`（選擇中心、中心卡片）、`arrival.`（到貨通知）、`stock.`（庫存讀取失敗）、`closure.`（休館公告）。
export const zh: Record<string, string> = {
  // 共用
  'borrow.reserve': '預約',
  'borrow.arrivalNotice': '到貨通知',
  'borrow.arrivalRegistered': '已登記到貨通知',
  'borrow.stockLeft': '剩餘: {n}',
  'borrow.waiting': '等待人數：{n}',
  'borrow.srItem': '：{text}',
  'borrow.srVariant': '：{category}，{name}',

  // 借用須知
  'borrow.rules.title': '二手輔具借用須知',
  'borrow.rules.checkingAccount': '正在確認帳號資料…',
  'borrow.rules.scrollHint': '請將須知內容滑至底部，再確認注意事項。',
  'borrow.rules.progress': '注意事項 {n}／{m}',
  'borrow.rules.complete': '已確認全部注意事項',
  'borrow.rules.reviewAgain': '重新檢查',
  'borrow.rules.centersHeading': '中心名稱、開放時間、中心地址、中心電話',
  'borrow.rules.consentIntro': '以下三點注意事項，閱畢請完成勾選，並點選下方「我同意」：',
  'borrow.rules.consentNote':
    '＊請參照＜衛生福利部疾病管制署＞公告之法定傳染病說明：https://www.cdc.gov.tw/Disease/Index',
  'borrow.rules.consentError': '請勾選以上三項注意事項。',
  'borrow.rules.disagree': '我不同意',
  'borrow.rules.agree': '我同意',

  // 選擇輔具（類別）
  'borrow.items.title': '選擇輔具',
  'borrow.items.lead': '請選擇您要借用的輔具',
  'borrow.items.backToCart': '回本次預約項目',
  'borrow.items.cartCount': '{n} 件',

  // 選擇種類（款式）
  'borrow.variants.title': '選擇種類',
  'borrow.variants.noStock': '目前二手{name}均無庫存',
  'borrow.variants.assessLink': '預約輔具評估，了解購買或租賃補助',
  'borrow.variants.height': '身高（公分）',
  'borrow.variants.weight': '體重（公斤）',
  'borrow.variants.fitTitle': '依使用者身高、體重篩選',
  'borrow.variants.fitRange': '請輸入 {min}–{max} 之間的整數',
  'borrow.variants.fitNone': '沒有符合的款式',
  'borrow.variants.fitMatch': '符合 {yes} 款',
  'borrow.variants.fitMatchUnknown': '符合 {yes} 款，{unknown} 款未標示',
  'borrow.variants.clearFit': '清除篩選',
  'borrow.variants.fitUnknown': '未標示適用身高體重',
  'borrow.variants.added': '已加入本次預約項目',

  // 本次預約項目
  'borrow.cart.title': '本次預約項目',
  'borrow.cart.empty': '尚未選擇輔具',
  'borrow.cart.remove': '刪除',
  'borrow.cart.more': '繼續選擇輔具',

  // 選擇中心
  'center.title': '選擇中心',
  'center.lead': '請選擇借用輔具中心',
  'center.locate': '依目前位置排序',
  'center.legend': '取貨中心',
  'center.nearest': '距離最近',
  'center.matchAddress': '鄰近您的地址',
  'center.nameTag': '{name}（{tag}）',
  'center.distance': '距離約 {km} 公里',
  'center.closed': '{date}休館',
  'center.closedReason': '{date}休館：{reason}',
  'center.sepSemi': '；',
  'center.sepList': '、',
  'center.pickup': '取貨期限 {deadline}，可前往：{dates}',
  'center.pickupNone': '取貨期限 {deadline}前未開館，無法於期限內取貨',
  'center.stockLeft': '此款尚餘 {n} 件',
  'center.stockNone': '此中心目前無此款',
  'center.allClosed': '取貨期限內三處中心均未開館，請於開館日再行預約。',
  'center.allClosedWarn':
    '取貨期限（2 天內，含當日）內三處中心均未開館，預約後恐無法如期取貨，逾期預約將自動取消。下一個開館日為 {date}。',
  'center.allClosedNext':
    '取貨期限（2 天內，含當日）內三處中心均未開館，暫時無法預約借用。下一個開館日為 {date}，請屆時再行預約。',
  'center.pickRequired': '請選擇一家取貨的輔具中心',
  'center.open': '開館中',
  'center.closedNow': '目前休館',

  // 到貨通知
  'arrival.registerHeading': '登記項目',
  'arrival.device': '輔具',
  'arrival.explain': '輔具到貨時將以台北通推播通知您；到貨通知不保留輔具，收到通知後請再行預約。',
  'arrival.undo': '取消登記',
  'arrival.notFound': '查無此輔具',
  'arrival.home': '回輔具預約',
  'arrival.failed': '送出失敗，請檢查網路後再試一次。',
  'arrival.duplicate': '同類輔具已登記到貨通知，同一類別僅可登記一項。',
  'arrival.unavailable': '此品項目前不開放登記到貨通知。',
  'arrival.number': '登記編號',
  'arrival.sending': '送出中…',
  'arrival.submit': '確認送出',
  'arrival.reservations': '服務預約查詢與取消',

  // 庫存讀取失敗
  'stock.title': '無法取得庫存資料',
  'stock.hint': '請檢查網路後再試一次。',

  // 休館公告
  'closure.title': '近期休館公告',
  'closure.line': '{center}輔具中心 {date} 休館',
  'closure.lineReason': '{center}輔具中心 {date} 休館：{reason}'
};
export const en: Record<string, string> = {
  // 共用
  'borrow.reserve': 'Reserve',
  'borrow.arrivalNotice': 'Arrival notice',
  'borrow.arrivalRegistered': 'Arrival notice registered',
  'borrow.stockLeft': 'Available: {n}',
  'borrow.waiting': 'People waiting: {n}',
  'borrow.srItem': ': {text}',
  'borrow.srVariant': ': {category}, {name}',

  // 借用須知
  'borrow.rules.title': 'Second-hand device loan rules',
  'borrow.rules.checkingAccount': 'Checking account…',
  'borrow.rules.scrollHint': 'Scroll to the end of the rules before confirming the notes.',
  'borrow.rules.progress': 'Note {n} of {m}',
  'borrow.rules.complete': 'All notes confirmed',
  'borrow.rules.reviewAgain': 'Review again',
  'borrow.rules.centersHeading': 'Center name, opening hours, address and phone',
  'borrow.rules.consentIntro':
    'Read the three notes below, tick each one, then select "I agree" below:',
  'borrow.rules.consentNote':
    '* For the list of legally notifiable infectious diseases, see the Taiwan Centers for Disease Control (Ministry of Health and Welfare): https://www.cdc.gov.tw/Disease/Index',
  'borrow.rules.consentError': 'Tick all three notes above.',
  'borrow.rules.disagree': 'I disagree',
  'borrow.rules.agree': 'I agree',

  // 選擇輔具（類別）
  'borrow.items.title': 'Choose a device',
  'borrow.items.lead': 'Choose the device you want to borrow',
  'borrow.items.backToCart': "Back to this reservation's items",
  'borrow.items.cartCount': '{n} selected',

  // 選擇種類（款式）
  'borrow.variants.title': 'Choose a type',
  'borrow.variants.noStock': 'Out of stock: second-hand {name}',
  'borrow.variants.assessLink': 'Reserve an assessment to learn about purchase or rental subsidies',
  'borrow.variants.height': 'Height (cm)',
  'borrow.variants.weight': 'Weight (kg)',
  'borrow.variants.fitTitle': 'Filter by the user height and weight',
  'borrow.variants.fitRange': 'Enter a whole number between {min} and {max}',
  'borrow.variants.fitNone': 'No matching models',
  'borrow.variants.fitMatch': 'Matching: {yes}',
  'borrow.variants.fitMatchUnknown': 'Matching: {yes}, not specified: {unknown}',
  'borrow.variants.clearFit': 'Clear filter',
  'borrow.variants.fitUnknown': 'Height and weight range not specified',
  'borrow.variants.added': 'Added to this reservation',

  // 本次預約項目
  'borrow.cart.title': 'Items in this reservation',
  'borrow.cart.empty': 'No device selected yet',
  'borrow.cart.remove': 'Remove',
  'borrow.cart.more': 'Choose more devices',

  // 選擇中心
  'center.title': 'Choose a center',
  'center.lead': 'Choose the assistive device center to borrow from',
  'center.locate': 'Sort by my current location',
  'center.legend': 'Pickup center',
  'center.nearest': 'Nearest',
  'center.matchAddress': 'Near your address',
  'center.nameTag': '{name} ({tag})',
  'center.distance': 'About {km} km away',
  'center.closed': 'Closed {date}',
  'center.closedReason': 'Closed {date}: {reason}',
  'center.sepSemi': '; ',
  'center.sepList': ', ',
  'center.pickup': 'Pickup deadline {deadline}. Open on: {dates}',
  'center.pickupNone':
    'Not open before the pickup deadline ({deadline}), so you cannot pick up here in time',
  'center.stockLeft': '{n} of this model left',
  'center.stockNone': 'This center has none of this model now',
  'center.allClosed':
    'All three centers are closed for the next few days. Please reserve another day.',
  'center.allClosedWarn':
    'All three centers are closed within the pickup deadline (2 days, including today), so you may not be able to collect in time and an overdue reservation is cancelled automatically. The next opening day is {date}.',
  'center.allClosedNext':
    'All three centers are closed within the pickup deadline (2 days, including today), so loans cannot be reserved right now. The next opening day is {date}; please come back then.',
  'center.pickRequired': 'Select an assistive device center for pickup',
  'center.open': 'Open now',
  'center.closedNow': 'Closed now',

  // 到貨通知
  'arrival.registerHeading': 'Registration details',
  'arrival.device': 'Device',
  'arrival.explain':
    'You will get a TownPass notification when the device arrives. The notice does not hold the device; please book it after you are notified.',
  'arrival.undo': 'Cancel registration',
  'arrival.notFound': 'Device not found',
  'arrival.home': 'Back to Assistive Devices',
  'arrival.failed': 'Could not submit. Check your connection and try again.',
  'arrival.duplicate':
    'You already have an arrival notice for this type of device. Only one per type is allowed.',
  'arrival.unavailable': 'Arrival notices are not available for this item right now.',
  'arrival.number': 'Registration number',
  'arrival.sending': 'Sending…',
  'arrival.submit': 'Confirm and submit',
  'arrival.reservations': 'View or cancel reservations',

  // 庫存讀取失敗
  'stock.title': 'Could not load stock data',
  'stock.hint': 'Check your connection and try again.',

  // 休館公告
  'closure.title': 'Upcoming closures',
  'closure.line': '{center} center closed {date}',
  'closure.lineReason': '{center} center closed {date}: {reason}'
};
