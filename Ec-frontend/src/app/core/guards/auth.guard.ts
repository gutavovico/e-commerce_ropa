import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);

  if (typeof window !== 'undefined') {
    const token =
      localStorage.getItem('fashionstore_token') ||
      sessionStorage.getItem('fashionstore_token');

    if (token) {
      return true;
    }
  }

  return router.createUrlTree(['/login']);
};
