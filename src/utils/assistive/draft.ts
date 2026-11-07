import type { ApplicantForm, PickupForm, ServiceId, UserForm } from './types';

/**
 * 申請草稿暫存在 sessionStorage：重新整理或網頁被重新載入時不用從頭填；
 * 關掉服務（WebView 結束）就會消失，不會留在手機上。
 * 身分證字號不存：本人申請時會從台北通資料重新帶入，替他人申請才需要再填一次。
 */
const KEY = 'assistive.draft';

export interface Draft {
  service: ServiceId;
  qualified: boolean | null;
  consents: boolean[];
  variant: { id: string; categoryName: string; name: string; spec: string } | null;
  needs: string[];
  needOther: string;
  repairNeeds: string[];
  repairOther: string;
  centerId: string;
  applicant: ApplicantForm;
  user: UserForm;
  pickup: PickupForm;
}

export const loadDraft = (): Draft | null => {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Draft) : null;
  } catch {
    return null;
  }
};

export const saveDraft = (draft: Draft) => {
  try {
    sessionStorage.setItem(KEY, JSON.stringify({ ...draft, user: { ...draft.user, idNo: '' } }));
  } catch {
    /* 儲存空間不可用：略過，只是重新整理後不會還原 */
  }
};

export const clearDraft = () => {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* 略過 */
  }
};
