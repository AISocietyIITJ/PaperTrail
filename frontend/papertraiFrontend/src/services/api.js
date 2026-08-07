import researchPathMock from '../mocks/researchPath.mock.json';
import facultyMatchesMock from '../mocks/facultyMatches.mock.json';
import problemCloudMock from '../mocks/problemCloud.mock.json';

const MOCK_DELAY = 600; // ms

function simulateNetwork(data) {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(data);
    }, MOCK_DELAY);
  });
}

export async function getResearchPath(query, maxHops = 3) {
  // In a real app, send query and maxHops to backend.
  return simulateNetwork(researchPathMock);
}

export async function getFacultyMatches(resumeFile, interests) {
  return simulateNetwork(facultyMatchesMock);
}

export async function getProblemCloud(query) {
  return simulateNetwork(problemCloudMock);
}
