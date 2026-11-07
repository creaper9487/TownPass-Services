import type { RouteRecordRaw, RouteRecordSingleView } from 'vue-router';
import { useAssistiveStore } from '@/stores/assistive';
import { flows } from '@/utils/assistive/services';
import type { ServiceId } from '@/utils/assistive/types';

const TITLE = '輔具預約';
const ALL = 'borrow|assess|recycle';

type Store = ReturnType<typeof useAssistiveStore>;

/** 每一步需要先完成什麼；直接開網址或重新整理時，會被帶回第一個沒完成的步驟 */
const isComplete = (step: string, s: Store) => {
  switch (step) {
    case 'qualify':
      return s.qualified === true;
    case 'rules':
      return s.consents.every(Boolean);
    case 'items':
      return !!s.variant;
    case 'center':
      return !!s.centerId;
    case 'need':
      return s.needs.length > 0 && (!s.needs.includes('其他') || !!s.needOther.trim());
    case 'contact':
      return !!s.applicant.name.trim() && !!s.applicant.mobile.trim();
    case 'user':
      return !!s.user.name.trim() && !!s.user.idNo.trim() && !!s.user.registeredDistrict;
    case 'pickup':
      return !!s.pickup.district && !!s.pickup.address.trim() && !!s.pickup.hasElevator;
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
        path: 'reservations/:id',
        name: 'assistive-reservation',
        component: () => import('@/views/assistive/ReservationDetailView.vue'),
        meta: { title: TITLE }
      },
      {
        path: 'faq',
        name: 'assistive-faq',
        component: () => import('@/views/assistive/FaqView.vue'),
        meta: { title: TITLE }
      },
      step('qualify', 'qualify', () => import('@/views/assistive/QualifyView.vue')),
      step('rules', 'rules', () => import('@/views/assistive/RulesView.vue'), 'borrow'),
      step('items', 'items', () => import('@/views/assistive/ItemsView.vue'), 'borrow'),
      {
        path: ':service(borrow)/items/:categoryId',
        name: 'assistive-variants',
        component: () => import('@/views/assistive/VariantsView.vue'),
        meta: { title: TITLE, step: 'items' },
        beforeEnter: (to) => {
          // 看種類之前同樣要通過資格與須知，但還沒選到輔具
          const store = useAssistiveStore();
          if (store.service !== 'borrow') store.begin('borrow');
          const missing = ['qualify', 'rules'].find((s) => !isComplete(s, store));
          return missing ? { name: `assistive-${missing}`, params: to.params } : true;
        }
      },
      step('center', 'center', () => import('@/views/assistive/CenterView.vue'), 'borrow'),
      step('need', 'need', () => import('@/views/assistive/NeedView.vue'), 'assess|recycle'),
      step('contact', 'contact', () => import('@/views/assistive/ContactView.vue')),
      step('user', 'user', () => import('@/views/assistive/UserView.vue'), 'assess'),
      step('pickup', 'pickup', () => import('@/views/assistive/PickupView.vue'), 'recycle'),
      step('review', 'review', () => import('@/views/assistive/ReviewView.vue')),
      step('done', 'done', () => import('@/views/assistive/DoneView.vue'))
    ]
  }
];
