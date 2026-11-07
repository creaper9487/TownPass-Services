/**
 * 資料值的英文顯示（資料本身一律維持中文，送後端和存本機的都是中文）。
 * 沒有收錄的就照原樣顯示中文。中心名稱用官方網站的英文名稱，其餘是我們的翻譯。
 */
export const dataEn: Record<string, string> = {
  // 品項類別
  輪椅: 'Wheelchair',
  助行器: 'Walker',
  拐杖: 'Crutches & canes',
  便盆椅: 'Commode chair',
  輪椅座墊: 'Wheelchair cushion',
  氣墊床: 'Air mattress',
  洗澡椅: 'Shower chair',
  助步車: 'Rollator',
  居家用照顧床: 'Home care bed',
  兒童類輔具: "Children's assistive devices",
  移位輔具: 'Transfer aids',
  其他: 'Other',
  // 評估、維修項目
  '居家用照顧床(病床)': 'Home care bed (hospital bed)',
  手動輪椅: 'Manual wheelchair',
  電動輪椅: 'Power wheelchair',
  居家無障礙: 'Home accessibility',
  '矯具/義具': 'Orthoses / prostheses',
  視障輔具: 'Visual aids',
  溝通輔具: 'Communication aids',
  電腦輔具: 'Computer access aids',
  爬梯機借用: 'Stair-climber loan',
  '拐杖/助行器': 'Crutches / walkers',
  // 行政區
  中山區: 'Zhongshan Dist.',
  大同區: 'Datong Dist.',
  士林區: 'Shilin Dist.',
  北投區: 'Beitou Dist.',
  內湖區: 'Neihu Dist.',
  信義區: 'Xinyi Dist.',
  文山區: 'Wenshan Dist.',
  南港區: 'Nangang Dist.',
  中正區: 'Zhongzheng Dist.',
  萬華區: 'Wanhua Dist.',
  大安區: "Da'an Dist.",
  松山區: 'Songshan Dist.',
  臺北市: 'Taipei City',
  // 輔具中心（官方英文名稱）
  臺北市合宜輔具中心: 'Assistive Devices Center',
  臺北市南區輔具中心: 'Taipei City South Dist. Assistive Technology Center',
  臺北市西區輔具中心: 'Taipei City West Dist. Assistive Technology Center',
  合宜: 'Heyi',
  南區: 'South Dist.',
  西區: 'West Dist.',
  // 休館原因（後端行事曆回傳的中文）
  例假日休館: 'Public holiday',
  國定假日: 'National holiday',
  臨時休館: 'Temporarily closed',
  // 選項
  是: 'Yes',
  否: 'No',
  男: 'Male',
  女: 'Female',
  有: 'Yes',
  無: 'No'
};
