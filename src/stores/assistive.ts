import { computed, ref, watch } from 'vue';
import { defineStore } from 'pinia';
import {
  centerByDistrict,
  centerById,
  centers,
  dateKey,
  nearestCenter,
  pickupWindow,
  upcomingClosures
} from '@/utils/assistive/centers';
import { fetchCenterCalendar } from '@/utils/assistive/api';
import { taipeiNow } from '@/utils/assistive/time';
import { districtFromAddress, isTwId } from '@/utils/assistive/validators';
import { services } from '@/utils/assistive/services';
import { clearDraft, loadDraft, saveDraft } from '@/utils/assistive/draft';
import type {
  ApplicantForm,
  CalendarDay,
  Center,
  PickupForm,
  Reservation,
  ServiceId,
  UserForm
} from '@/utils/assistive/types';

export interface Account {
  name: string;
  mobile: string;
  email: string;
  idNo: string;
  district: string;
}

export interface SelectedVariant {
  id: string;
  categoryName: string;
  name: string;
  spec: string;
}

const blankApplicant = (): ApplicantForm => ({
  name: '',
  mobile: '',
  phone: '',
  gender: '',
  email: ''
});
const blankUser = (): UserForm => ({
  name: '',
  idNo: '',
  gender: '',
  registeredDistrict: '',
  livingCounty: '臺北市',
  livingDistrict: '',
  remark: ''
});
const blankPickup = (): PickupForm => ({
  district: '',
  address: '',
  hasElevator: '',
  needCertificate: false,
  remark: ''
});

const genderFromId = (idNo: string): ApplicantForm['gender'] => {
  if (!isTwId(idNo)) return '';
  return idNo[1] === '1' ? 'M' : idNo[1] === '2' ? 'F' : '';
};

export const useAssistiveStore = defineStore('assistive', () => {
  const service = ref<ServiceId>('borrow');
  const qualified = ref<boolean | null>(null);
  const consents = ref<boolean[]>([false, false, false]);
  const variant = ref<SelectedVariant | null>(null);
  const needs = ref<string[]>([]);
  const needOther = ref('');
  /** 評估、維修合併表單裡「申請維修」的勾選項與其他 */
  const repairNeeds = ref<string[]>([]);
  const repairOther = ref('');
  const centerId = ref('');
  const applicant = ref<ApplicantForm>(blankApplicant());
  const user = ref<UserForm>(blankUser());
  const pickup = ref<PickupForm>(blankPickup());
  const submitted = ref<Reservation | null>(null);

  // 還原重新整理前的草稿；從首頁重新開始時 begin() 會清掉。
  let draftActive = true;
  const draft = loadDraft();
  if (draft) {
    service.value = draft.service ?? service.value;
    qualified.value = draft.qualified ?? null;
    consents.value = draft.consents ?? consents.value;
    variant.value = draft.variant ?? null;
    needs.value = draft.needs ?? [];
    needOther.value = draft.needOther ?? '';
    repairNeeds.value = draft.repairNeeds ?? [];
    repairOther.value = draft.repairOther ?? '';
    centerId.value = draft.centerId ?? '';
    applicant.value = { ...applicant.value, ...draft.applicant };
    user.value = { ...user.value, ...draft.user };
    pickup.value = { ...pickup.value, ...draft.pickup };
  }
  watch(
    [
      service,
      qualified,
      consents,
      variant,
      needs,
      needOther,
      repairNeeds,
      repairOther,
      centerId,
      applicant,
      user,
      pickup
    ],
    () => {
      if (!draftActive) return;
      saveDraft({
        service: service.value,
        qualified: qualified.value,
        consents: consents.value,
        variant: variant.value,
        needs: needs.value,
        needOther: needOther.value,
        repairNeeds: repairNeeds.value,
        repairOther: repairOther.value,
        centerId: centerId.value,
        applicant: applicant.value,
        user: user.value,
        pickup: pickup.value
      });
    },
    { deep: true }
  );

  /** 台北通帳號資料（App 內才有） */
  const account = ref<Account | null>(null);
  /** 使用者目前位置（使用者主動允許後才有） */
  const location = ref<{ lat: number; lng: number } | null>(null);

  /** 位置取不到（例如使用者沒有授權、或系統定位被拒絕）的次數，讓畫面能立刻反應而不是乾等逾時 */
  const locationFailures = ref(0);

  /** 款式篩選：使用者輸入的身高與體重（只在這個流程內保留，不存起來） */
  const fit = ref({ height: '', weight: '' });

  /** 各中心的逐日行事曆；null 代表沒有資料，畫面退回依星期判斷 */
  const calendars = ref<Record<string, CalendarDay[] | null>>({});
  const loadCalendars = async () => {
    const now = taipeiNow();
    const from = dateKey(now);
    const to = dateKey(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 14));
    await Promise.all(
      centers.map(async (c) => {
        if (c.id in calendars.value) return;
        calendars.value[c.id] = await fetchCenterCalendar(c.id, from, to);
      })
    );
  };
  const windowFor = (c: Center, now?: Date) => pickupWindow(c, now, calendars.value[c.id]);
  const closureNotices = computed(() =>
    centers
      .flatMap((c) => upcomingClosures(c, calendars.value[c.id]))
      .sort((a, b) => a.date.getTime() - b.date.getTime())
  );

  const homeDistrict = computed(() => account.value?.district || '');

  /** 依位置或帳號地址推薦的中心 */
  const recommendedCenter = computed(() => {
    if (location.value) return nearestCenter(location.value.lat, location.value.lng);
    return centerByDistrict(homeDistrict.value);
  });
  const recommendedBy = computed<'location' | 'address' | ''>(() =>
    location.value ? 'location' : homeDistrict.value && recommendedCenter.value ? 'address' : ''
  );

  /** 這張單實際會送到哪一個中心 */
  const center = computed(() => {
    switch (service.value) {
      case 'borrow':
        return centerById(centerId.value);
      case 'assess': {
        const district =
          user.value.livingCounty === '臺北市' && user.value.livingDistrict
            ? user.value.livingDistrict
            : user.value.registeredDistrict;
        return centerByDistrict(district);
      }
      case 'recycle':
        return centerByDistrict(pickup.value.district);
      default:
        return undefined;
    }
  });

  const withOther = (list: string[], other: string) =>
    list.map((item) => (item === '其他' && other.trim() ? `其他：${other.trim()}` : item));

  const needSummary = computed(() => {
    if (service.value === 'assess') {
      return [
        ...withOther(needs.value, needOther.value).map((i) => `申請評估：${i}`),
        ...withOther(repairNeeds.value, repairOther.value).map((i) => `申請維修：${i}`)
      ];
    }
    return withOther(needs.value, needOther.value);
  });

  const summary = computed(() => {
    if (service.value === 'borrow' && variant.value) {
      const v = variant.value;
      return [
        [v.categoryName, v.name, v.spec].filter((s) => s && s !== '---' && s !== '--').join('・')
      ];
    }
    return needSummary.value;
  });

  /** 開始一次新的申請：保留帳號與位置，其餘清空 */
  const begin = (id: ServiceId) => {
    draftActive = true;
    fit.value = { height: '', weight: '' };
    service.value = id;
    qualified.value = null;
    consents.value = [false, false, false];
    variant.value = null;
    needs.value = [];
    needOther.value = '';
    repairNeeds.value = [];
    repairOther.value = '';
    centerId.value = '';
    applicant.value = blankApplicant();
    user.value = blankUser();
    pickup.value = blankPickup();
    submitted.value = null;
    applyAccount();
  };

  /** 送出成功：記下結果，並清掉暫存的草稿（個資不再留著） */
  const finishSubmit = (reservation: Reservation) => {
    submitted.value = reservation;
    draftActive = false;
    clearDraft();
  };

  const setAccount = (data: Record<string, unknown>) => {
    const text = (v: unknown) => (typeof v === 'string' ? v.trim() : '');
    const addresses = Array.isArray(data.addresses)
      ? (data.addresses as Record<string, unknown>[])
      : [];
    const district =
      districtFromAddress(text(data.residentAddress)) ||
      addresses.map((a) => districtFromAddress(`${text(a.city)}${text(a.town)}`)).find(Boolean) ||
      '';
    account.value = {
      name: text(data.realName) || text(data.username),
      mobile: text(data.phoneNo),
      email: text(data.email),
      idNo: text(data.idNo).toUpperCase(),
      district
    };
    applyAccount();
  };

  /** 只補空欄位，不覆蓋使用者已經改過的內容 */
  const applyAccount = () => {
    const a = account.value;
    if (!a) return;
    const f = applicant.value;
    if (!f.name) f.name = a.name;
    if (!f.mobile) f.mobile = a.mobile;
    if (!f.email) f.email = a.email;
    if (!f.gender) f.gender = genderFromId(a.idNo);
    if (!user.value.registeredDistrict && a.district) user.value.registeredDistrict = a.district;
    if (!user.value.livingDistrict && a.district) user.value.livingDistrict = a.district;
    if (!pickup.value.district && a.district) pickup.value.district = a.district;
  };

  /**
   * 「同聯絡人」：把聯絡人的姓名、性別帶到輔具使用者；
   * 聯絡人就是台北通帳號本人時，也一併帶入身分證字號與行政區。
   */
  const fillUserFromContact = () => {
    user.value.name = applicant.value.name;
    user.value.gender = applicant.value.gender;
    const a = account.value;
    if (a && a.name === applicant.value.name) {
      if (a.idNo) user.value.idNo = a.idNo;
      if (a.district) {
        user.value.registeredDistrict = a.district;
        user.value.livingDistrict = a.district;
      }
    }
  };

  return {
    service,
    qualified,
    consents,
    variant,
    needs,
    needOther,
    centerId,
    applicant,
    user,
    pickup,
    submitted,
    account,
    location,
    locationFailures,
    homeDistrict,
    recommendedCenter,
    recommendedBy,
    center,
    needSummary,
    repairNeeds,
    repairOther,
    summary,
    fit,
    calendars,
    loadCalendars,
    windowFor,
    closureNotices,
    begin,
    finishSubmit,
    setAccount,
    applyAccount,
    fillUserFromContact
  };
});
