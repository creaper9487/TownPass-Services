// 輔具預約「assess」區的介面文字。key 一律以 `assess.`、`form.`、`contact.`、`user.`、`need.` 開頭。
export const zh: Record<string, string> = {
  // 共用表單元件
  'form.parens': '（{text}）',
  'form.required': '（必填）',
  'form.choose': '請選擇',
  'form.errorCount': '有 {n} 個欄位需要修正',
  'form.errorCountOne': '有 {n} 個欄位需要修正',
  'form.name': '姓名',
  'form.phone': '電話',
  'form.mobile': '手機',
  'form.gender': '性別',
  'form.email': 'E-mail',
  'form.remark': '備註',
  'form.idNo': '身分證字號',
  'form.emailHint': '將以此email寄送預約單',
  'form.err.name': '請輸入姓名',
  'form.err.email': 'E-mail 格式不正確',

  // 申請評估／維修：選擇項目
  'need.group.assess': '申請評估',
  'need.group.repair': '申請維修',
  'need.tabsLabel': '申請項目',
  'need.tabCount': '{title}（{n}）',
  'need.tabCountLabel': '{title}，已選 {n} 項',
  'need.err.pickOne': '請至少勾選一項',
  'need.err.other': '請填寫其他項目',
  'need.err.otherIn': '{title}：請填寫其他項目',

  // 聯絡人資料
  'contact.title': '聯絡人資料',
  'contact.fromAccount': '已帶入台北通資料',
  'contact.phoneHint': 'ex:0224597892 (將以此欄位進行預約查詢)',
  'contact.err.mobileRequired': '請輸入手機',
  'contact.err.mobile': '手機號碼須為 09 開頭之 10 碼數字，例如 0912345678',
  'contact.err.phoneRequired': '請輸入電話',
  'contact.err.phone': '電話請含區碼，例如 0224597892',
  'contact.err.gender': '請選擇性別',

  // 輔具使用者資料
  'user.title': '輔具使用者資料',
  'user.sameAsContact': '同聯絡人',
  'user.registeredDistrict': '戶籍地行政區',
  'user.livingDistrict': '居住地行政區',
  'user.err.idRequired': '請輸入身分證字號',
  'user.err.id': '身分證字號格式不正確，請重新確認',
  'user.err.registered': '請選擇戶籍地行政區'
};
export const en: Record<string, string> = {
  // Shared form components
  'form.parens': '({text})',
  'form.required': '(required)',
  'form.choose': 'Select',
  'form.errorCount': '{n} fields need correcting',
  'form.errorCountOne': '{n} field needs correcting',
  'form.name': 'Name',
  'form.phone': 'Phone',
  'form.mobile': 'Mobile',
  'form.gender': 'Gender',
  'form.email': 'Email',
  'form.remark': 'Notes',
  'form.idNo': 'ID number',
  'form.emailHint': 'Your booking confirmation will be sent to this email',
  'form.err.name': 'Enter a name',
  'form.err.email': 'Enter a valid email address',

  // Assessment / repair: choose items
  'need.group.assess': 'Assessment',
  'need.group.repair': 'Repair',
  'need.tabsLabel': 'Application type',
  'need.tabCount': '{title} ({n})',
  'need.tabCountLabel': '{title}, {n} selected',
  'need.err.pickOne': 'Select at least one item',
  'need.err.other': 'Enter the other item',
  'need.err.otherIn': '{title}: Enter the other item',

  // Contact details
  'contact.title': 'Contact details',
  'contact.fromAccount': 'Filled in from your TaipeiPass account',
  'contact.phoneHint': 'e.g. 0224597892 (used to look up your booking)',
  'contact.err.mobileRequired': 'Enter a mobile number',
  'contact.err.mobile': 'Mobile number must be 10 digits starting with 09, e.g. 0912345678',
  'contact.err.phoneRequired': 'Enter a phone number',
  'contact.err.phone': 'Include the area code, e.g. 0224597892',
  'contact.err.gender': 'Select a gender',

  // Device user details
  'user.title': 'Device user details',
  'user.sameAsContact': 'Same as contact',
  'user.registeredDistrict': 'Household registration district',
  'user.livingDistrict': 'District of residence',
  'user.err.idRequired': 'Enter an ID number',
  'user.err.id': 'ID number format is incorrect. Check it and try again',
  'user.err.registered': 'Select the household registration district'
};
