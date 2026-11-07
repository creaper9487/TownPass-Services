import type { RouteRecordRaw, RouteRecordSingleView } from 'vue-router';
import { useAssistiveStore } from '@/stores/assistive';
import { flows } from '@/utils/assistive/services';
import type { ServiceId } from '@/utils/assistive/types';
import { useAssistiveWelfareStore } from '@/stores/assistiveWelfare';

const TITLE = '輔具預約';
const ALL = 'borrow|assess';

type Store = ReturnType<typeof useAssistiveStore>;

const listOk = (list: string[], other: string) => !list.includes('其他') || !!other.trim();
/** 評估、維修可分開勾選，至少要有一項，且勾了「其他」就要填內容 */
const needDone = (s: Store) => {
  const picked = s.needs.length + (s.service === 'assess' ? s.repairNeeds.length : 0);
  return (
    picked > 0 &&
    listOk(s.needs, s.needOther) &&
    (s.service !== 'assess' || listOk(s.repairNeeds, s.repairOther))
  );
};

/** 每一步需要先完成什麼；直接開網址或重新整理時，會被帶回第一個沒完成的步驟 */
const isComplete = (step: string, s: Store) => {
  switch (step) {
    case 'rules':
      return s.consents.every(Boolean);
    case 'items':
      return !!s.variant;
    case 'center':
      return !!s.centerId;
    case 'need':
      return needDone(s);
    case 'contact':
      return !!s.applicant.name.trim() && !!s.applicant.mobile.trim();
    case 'user':
      return !!s.user.name.trim() && !!s.user.idNo.trim() && !!s.user.registeredDistrict;
    default:
      return true;
  }
};

const guard = (step: string) => (to: { params: Record<string, unknown> }) => {
  const store = useAssistiveStore();
  const service = to.params.service as ServiceId;

  if (step === 'done') return store.submitted ? true : { name: 'assistive-home' };
  if (step === 'review' && store.submitted) return { name: 'assistive-done', params: { service } };

  if (store.service !== service) store.begin(service);

  const steps = flows[service];
  const target = steps.indexOf(step);
  const missing = steps.slice(0, target).find((s) => !isComplete(s, store));
  return missing ? { name: `assistive-${missing}`, params: { service } } : true;
};

const step = (
  path: string,
  name: string,
  component: RouteRecordSingleView['component'],
  services = ALL
): RouteRecordSingleView => ({
  path: `:service(${services})/${path}`,
  name: `assistive-${name}`,
  component,
  meta: { title: TITLE, step: name },
  beforeEnter: guard(name)
});

export const assistiveRoutes: RouteRecordRaw[] = [
  {
    path: '/assistive',
    component: () => import('@/views/assistive/AssistiveLayout.vue'),
    meta: { title: TITLE },
    children: [
      {
        path: '',
        name: 'assistive-home',
        component: () => import('@/views/assistive/HomeView.vue'),
        meta: { title: TITLE }
      },
      {
        path: 'reservations',
        name: 'assistive-reservations',
        component: () => import('@/views/assistive/ReservationsView.vue'),
        meta: { title: TITLE }
      },
      {
        path: 'welfare',
        name: 'assistive-welfare',
        component: () => import('@/views/assistive/WelfareIntroView.vue'),
        meta: { title: TITLE }
      },
      {
        path: 'welfare/question/:id',
        name: 'assistive-welfare-question',
        component: () => import('@/views/assistive/WelfareQuestionView.vue'),
        meta: { title: TITLE },
        // 直接開網址或重新整理時沒有作答進度，回到說明頁重新開始
        beforeEnter: (to) =>
          useAssistiveWelfareStore().trail.includes(String(to.params.id))
            ? true
            : { name: 'assistive-welfare' }
      },
      {
        path: 'welfare/result',
        name: 'assistive-welfare-result',
        component: () => import('@/views/assistive/WelfareResultView.vue'),
        meta: { title: TITLE },
        beforeEnter: () =>
          useAssistiveWelfareStore().finished ? true : { name: 'assistive-welfare' }
      },
      {
        path: 'welfare/page/:slug',
        name: 'assistive-welfare-page',
        component: () => import('@/views/assistive/WelfarePageView.vue'),
        meta: { title: TITLE }
      },
      {
        path: 'arrival/:variantId',
        name: 'assistive-arrival',
        component: () => import('@/views/assistive/ArrivalView.vue'),
        meta: { title: TITLE }
      },
      {
        path: 'reservations/:id',
        name: 'assistive-reservation',
        component: () => import('@/views/assistive/ReservationDetailView.vue'),
        meta: { title: TITLE }
      },
      step('rules', 'rules', () => import('@/views/assistive/RulesView.vue'), 'borrow'),
      step('items', 'items', () => import('@/views/assistive/ItemsView.vue'), 'borrow'),
      {
        path: ':service(borrow)/items/:categoryId',
        name: 'assistive-variants',
        component: () => import('@/views/assistive/VariantsView.vue'),
        meta: { title: TITLE, step: 'items' },
        beforeEnter: (to) => {
          // 看種類之前同樣要先同意須知，但還沒選到輔具
          const store = useAssistiveStore();
          if (store.service !== 'borrow') store.begin('borrow');
          return isComplete('rules', store) ? true : { name: 'assistive-rules', params: to.params };
        }
      },
      step('center', 'center', () => import('@/views/assistive/CenterView.vue'), 'borrow'),
      step('need', 'need', () => import('@/views/assistive/NeedView.vue'), 'assess'),
      step('contact', 'contact', () => import('@/views/assistive/ContactView.vue')),
      step('user', 'user', () => import('@/views/assistive/UserView.vue'), 'assess'),
      step('review', 'review', () => import('@/views/assistive/ReviewView.vue')),
      step('done', 'done', () => import('@/views/assistive/DoneView.vue'))
    ]
  }
];
