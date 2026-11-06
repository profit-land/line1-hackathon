# 1호선톤 Frontend

Vite + React 19 + TypeScript + Tailwind CSS v4 + React Router

## 시작하기

```bash
cd frontend
npm install
cp .env.example .env.local   # 필요 시 값 수정
npm run dev                   # http://localhost:5173
```

## 스크립트

| 명령 | 설명 |
| --- | --- |
| `npm run dev` | 개발 서버 (같은 네트워크의 폰에서도 접속 가능) |
| `npm run build` | 타입체크 + 프로덕션 빌드 (`dist/`) |
| `npm run preview` | 빌드 결과 미리보기 |
| `npm run lint` | oxlint |
| `npm run format` | prettier 포맷 |
| `npm run typecheck` | 타입체크만 |

## 구조

```
src/
  pages/        라우트 단위 화면 (화면 시안 ID 기준, 예: A-2)
  components/   공용 컴포넌트
  lib/          API 클라이언트, 유틸
  App.tsx       라우팅
```

- import 경로 alias: `@/` → `src/` (예: `import HomePage from '@/pages/HomePage'`)
- 환경변수는 `VITE_` 접두사만 브라우저에서 `import.meta.env.VITE_*` 로 접근 가능

## 와이어프레임

정적 와이어프레임 스냅샷은 `public/wireframe/`에 있습니다. `npm run dev` 실행 후
http://localhost:5173/wireframe/index.html 에서 화면 목록을 볼 수 있습니다.
원본은 `design-collab/wireframe/`입니다.
