import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'dashboard',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then(
        (m) => m.DashboardComponent
      ),
  },
  {
    path: 'alert-detail',
    loadComponent: () =>
      import('./features/alert-detail/alert-detail.component').then(
        (m) => m.AlertDetailComponent
      ),
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
