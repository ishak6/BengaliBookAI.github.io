# Bengali Book AI — কাজের তালিকা

শেষ আপডেট: 2026-11-13

যাচাই ছাড়া কোনো কাজ Done করা যাবে না।

## কোডে যুক্ত
- [x] Bengali ও English Tesseract OCR language package install ও workflow-এ language verification.
- [x] Native PDF text quality কম হলে OCR fallback.
- [x] Tesseract PSM 6 ও PSM 11 ফল তুলনা করে text নির্বাচন.
- [x] Worker page batch upload-এ transient HTTP retry এবং accepted page count যাচাই.
- [x] OCR quality unit tests ও Python syntax validation CI-তে চালানো.
- [x] সর্বশেষ Quality Harness run সফল: https://github.com/ishak6/BengaliBookAI.github.io/actions/runs/43422722782

## বাস্তব PDF indexing — এখনও অসম্পন্ন
- [ ] Index PDF workflow-এর বাস্তব run সফলভাবে চালানো.
- [ ] আগে upload করা দুই PDF-এর প্রত্যেকটির Book ID, indexed page count এবং Worker/D1 status যাচাই.
- [ ] Bengali scanned PDF-এর page text হাতে যাচাই: মাত্রা, যুক্তাক্ষর, page order ও citation.
- [ ] Human-verified Bengali OCR benchmark তৈরি.
- [ ] বড় ও mixed native-text/scanned PDF-এ runtime ও memory পরীক্ষা.

## GitHub-এ পাওয়া তথ্য
- [x] Releases-এ দুইটি PDF asset পাওয়া গেছে: Students.hack.pdf এবং দুধ ভাত — ইন্দিরা দেবী চৌধুরানী PDF.
- [ ] এই দুটি release asset-কে admin library-র সঠিক Book ID ও status-এর সঙ্গে মিলিয়ে দেখা বাকি.
- [ ] সর্বশেষ repository Actions তালিকায় Index PDF workflow-এর কোনো run পাওয়া যায়নি; তাই বাস্তব OCR/indexing সফল বলা যাচ্ছে না.

## নির্ভরতা / বাধা
- Manual Index PDF run-এর জন্য প্রতিটি বইয়ের সঠিক Book ID ও release URL প্রয়োজন.
- Worker Admin API access-এর জন্য WORKER_ADMIN_API_TOKEN secret থাকতে হবে.
- Cover upload-এর জন্য Actions GITHUB_TOKEN-এ contents:write permission প্রয়োজন.
- Cloudflare Worker ও D1 production-এ সচল থাকতে হবে.
- বর্তমান GitHub connection দিয়ে workflow_dispatch চালু করার write action উপলব্ধ নয়; তাই এই run এখান থেকে trigger করা যায়নি.
- বাস্তব PDF run না হওয়া পর্যন্ত production OCR verified বলা যাবে না.

## কাজের সীমা
- admin.html এবং soo.html এই OCR পরিবর্তনের অংশ নয়; আলাদা নির্দেশ ছাড়া পরিবর্তন করা হবে না.
- বইয়ের public-domain/open-license/permission অধিকার নিশ্চিত না হলে public indexing করা যাবে না.
- কোনো বাস্তব run ব্যর্থ হলে এখানে error, কারণ ও পরবর্তী পদক্ষেপ লিখতে হবে.
